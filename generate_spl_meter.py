#!/usr/bin/env python3
"""
SPL Meter - Python Backend Version
===================================

A local SPL measurement application where:
- Python handles all audio capture and SPL calculations
- HTML/JS is just the visual display
- Communication via WebSocket for real-time updates

This avoids browser microphone permission issues and provides more accurate
measurements using PyAudio instead of Web Audio API.

Requirements:
    pip install pyaudio websockets

Usage:
    python spl_meter_server.py [--port 8000] [--html spl_display.html]

Then open http://localhost:8000 in your browser.
"""

import argparse
import asyncio
import json
import math
import struct
import time
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
import pyaudio
import websockets


class SPLCalculator:
    """Handles all SPL calculation logic."""
    
    # Calibration offsets for different microphone types
    CALIBRATION = {
        'umik1': 128,      # UMIK-1: -34 dBFS at 94 dB SPL
        'default': 94,      # Generic microphone approximation
        'builtin': 94,      # Built-in laptop/desktop mics
    }
    
    # Sample rate and chunk size
    SAMPLE_RATE = 44100
    CHUNK_SIZE = 1024
    
    def __init__(self, mic_type='default'):
        """
        Initialize SPL calculator.
        
        Args:
            mic_type: Type of microphone ('umik1', 'default', 'builtin')
        """
        self.mic_type = mic_type
        self.offset = self.CALIBRATION.get(mic_type, 94)
        self.audio = None
        self.stream = None
        
    def start_audio(self):
        """Start PyAudio stream."""
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.SAMPLE_RATE,
            input=True,
            frames_per_buffer=self.CHUNK_SIZE
        )
        print(f"Audio stream started with {self.mic_type} calibration (offset: +{self.offset} dB)")
        
    def stop_audio(self):
        """Stop PyAudio stream."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()
        self.stream = None
        self.audio = None
        
    def calculate_spl(self, audio_data):
        """
        Calculate SPL from raw audio data.
        
        Args:
            audio_data: Raw bytes from PyAudio stream
            
        Returns:
            dict: SPL reading with instant, averages, and peaks
        """
        # Convert bytes to numpy-like array (using struct for speed)
        # Format: little-endian signed short (paInt16)
        num_samples = len(audio_data) // 2
        samples = struct.unpack(f'<{num_samples}h', audio_data)
        
        # Calculate RMS
        sum_squares = sum(s * s for s in samples)
        rms = math.sqrt(sum_squares / num_samples) if num_samples > 0 else 0
        
        # Handle zero RMS (silence)
        if rms == 0:
            return {'instant': 0.0, 'rms': 0.0, 'dbfs': float('-inf')}
        
        # Convert to dBFS
        dbfs = 20 * math.log10(rms / 32768.0)  # 32768 = max 16-bit value
        
        # Convert to SPL using calibration offset
        spl = dbfs + self.offset
        
        # Clamp to reasonable range
        spl = max(0, min(140, spl))
        
        # Apply A-weighting approximation
        spl = self.apply_a_weighting(spl)
        
        return {
            'instant': round(spl, 1),
            'rms': round(rms, 4),
            'dbfs': round(dbfs, 1)
        }
    
    def apply_a_weighting(self, spl):
        """
        Apply A-weighting curve approximation.
        
        Note: This is a simplified approximation. For accurate A-weighting,
        FFT analysis would be needed to apply frequency-dependent corrections.
        
        Args:
            spl: SPL value in dB
            
        Returns:
            float: SPL with A-weighting applied
        """
        # Simple approximation: subtract ~2 dB for typical speech/music
        # Real A-weighting would require FFT and frequency-based correction
        return spl - 2


class SPLDataManager:
    """Manages SPL data storage and time-weighted averages."""
    
    def __init__(self):
        self.readings = []
        self.one_min_readings = []
        self.one_hour_readings = []
        self.eight_hour_readings = []
        self.peak_1min = -float('inf')
        self.peak_all = -float('inf')
        self.peak_1min_reset_time = None
        
    def add_reading(self, spl, timestamp=None):
        """
        Add a new SPL reading and update all time windows.
        
        Args:
            spl: SPL value in dB
            timestamp: Optional timestamp (defaults to current time)
            
        Returns:
            dict: Complete reading with all calculated values
        """
        if timestamp is None:
            timestamp = time.time()
        
        reading = {
            'timestamp': timestamp,
            'instant': spl,
            'one_min_avg': None,
            'one_hour_avg': None,
            'eight_hour_avg': None,
            'peak': spl
        }
        
        # Add to all storage
        self.readings.append(reading)
        self.one_min_readings.append(reading)
        self.one_hour_readings.append(reading)
        self.eight_hour_readings.append(reading)
        
        # Clean up old readings
        now = timestamp
        
        # 1 minute window
        cutoff_1min = now - 60
        self.one_min_readings = [r for r in self.one_min_readings if r['timestamp'] >= cutoff_1min]
        
        # 1 hour window (clean every 10 readings to reduce overhead)
        if len(self.readings) % 10 == 0:
            cutoff_1hr = now - 3600
            self.one_hour_readings = [r for r in self.one_hour_readings if r['timestamp'] >= cutoff_1hr]
        
        # 8 hour window (clean every 60 readings)
        if len(self.readings) % 60 == 0:
            cutoff_8hr = now - 28800
            self.eight_hour_readings = [r for r in self.eight_hour_readings if r['timestamp'] >= cutoff_8hr]
        
        # Calculate time-weighted averages (Leq)
        reading['one_min_avg'] = self.calculate_leq(self.one_min_readings)
        reading['one_hour_avg'] = self.calculate_leq(self.one_hour_readings)
        reading['eight_hour_avg'] = self.calculate_leq(self.eight_hour_readings)
        
        # Update peaks
        if self.peak_1min_reset_time is None or timestamp >= self.peak_1min_reset_time + 60:
            # Reset 1-minute peak
            self.peak_1min = spl
            self.peak_1min_reset_time = timestamp
        else:
            self.peak_1min = max(self.peak_1min, spl)
        
        self.peak_all = max(self.peak_all, spl)
        
        # Round values for display
        reading['one_min_avg'] = round(reading['one_min_avg'], 1)
        reading['one_hour_avg'] = round(reading['one_hour_avg'], 1)
        reading['eight_hour_avg'] = round(reading['eight_hour_avg'], 1)
        reading['peak'] = round(self.peak_1min, 1)
        
        # Limit history
        if len(self.readings) > 300:  # 5 minutes at ~10 readings/sec
            self.readings.pop(0)
        
        return reading
    
    def calculate_leq(self, readings):
        """
        Calculate Leq (Equivalent Continuous Sound Level) for a set of readings.
        
        Leq = 10 * log10( (1/n) * sum(10^(Li/10)) )
        
        Args:
            readings: List of reading dictionaries
            
        Returns:
            float: Leq value in dB
        """
        if not readings:
            return 0.0
        
        sum_energy = sum(10 ** (r['instant'] / 10) for r in readings)
        avg_energy = sum_energy / len(readings)
        leq = 10 * math.log10(avg_energy) if avg_energy > 0 else 0.0
        
        return leq if math.isfinite(leq) else 0.0
    
    def get_latest_reading(self):
        """Get the most recent complete reading."""
        if self.readings:
            return self.readings[-1]
        return None
    
    def get_stats(self):
        """Get current statistics for display."""
        latest = self.get_latest_reading()
        if not latest:
            return {
                'instant': 0.0,
                'one_min_avg': 0.0,
                'one_hour_avg': 0.0,
                'eight_hour_avg': 0.0,
                'peak_1min': 0.0,
                'peak_all': 0.0
            }
        
        return {
            'instant': latest['instant'],
            'one_min_avg': latest['one_min_avg'],
            'one_hour_avg': latest['one_hour_avg'],
            'eight_hour_avg': latest['eight_hour_avg'],
            'peak_1min': self.peak_1min if self.peak_1min != -float('inf') else 0.0,
            'peak_all': self.peak_all if self.peak_all != -float('inf') else 0.0
        }


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Threaded HTTP server to handle multiple requests."""
    allow_reuse_address = True


class QuietHTTPHandler(SimpleHTTPRequestHandler):
    """HTTP handler that doesn't log requests."""
    
    def log_message(self, format, *args):
        pass
    
    def do_GET(self):
        """Serve files, with special handling for root path."""
        if self.path == '/' or self.path == '/index.html':
            # Serve the display HTML
            self.path = '/spl_display.html'
        return SimpleHTTPRequestHandler.do_GET(self)


async def websocket_handler(websocket, path, data_manager):
    """
    WebSocket handler that streams SPL data to connected clients.
    
    Args:
        websocket: WebSocket connection
        path: Request path
        data_manager: SPLDataManager instance
    """
    print(f"WebSocket client connected from {websocket.remote_address}")
    
    try:
        # Send initial stats
        stats = data_manager.get_stats()
        stats['type'] = 'stats'
        await websocket.send(json.dumps(stats))
        
        # Keep connection open and send updates
        while True:
            latest = data_manager.get_latest_reading()
            if latest:
                # Format timestamp for display
                timestamp_str = time.strftime('%H:%M:%S', time.localtime(latest['timestamp']))
                
                message = {
                    'type': 'reading',
                    'timestamp': timestamp_str,
                    'instant': latest['instant'],
                    'one_min_avg': latest['one_min_avg'],
                    'one_hour_avg': latest['one_hour_avg'],
                    'eight_hour_avg': latest['eight_hour_avg'],
                    'peak': latest['peak'],
                    'stats': data_manager.get_stats()
                }
                await websocket.send(json.dumps(message))
            
            # Send updates at ~10 Hz (100ms intervals)
            await asyncio.sleep(0.1)
            
    except websockets.exceptions.ConnectionClosed:
        print(f"WebSocket client disconnected from {websocket.remote_address}")
    except Exception as e:
        print(f"WebSocket error: {e}")


async def start_websocket_server(port, data_manager):
    """
    Start WebSocket server for real-time data streaming.
    
    Args:
        port: Port to listen on
        data_manager: SPLDataManager instance
    """
    server = await websockets.serve(
        lambda ws, path: websocket_handler(ws, path, data_manager),
        'localhost',
        port + 1  # Use port+1 for WebSocket
    )
    print(f"WebSocket server started on ws://localhost:{port + 1}")
    await server.wait_closed()


HTML_DISPLAY = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SPL Meter - Display</title>
    <style>
        :root {
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --bg-card: #0f3460;
            --text-primary: #eaeaea;
            --text-secondary: #a0a0a0;
            --accent: #e94560;
            --accent-glow: rgba(233, 69, 96, 0.5);
            --success: #4ecca3;
            --warning: #ffc107;
            --danger: #ff4444;
            --border: #2a2a4a;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        header { text-align: center; margin-bottom: 30px; }
        h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(135deg, var(--accent), var(--success));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .subtitle { color: var(--text-secondary); font-size: 1.1rem; }
        .status-bar {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 15px 20px;
            border: 1px solid var(--border);
            margin-bottom: 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }
        .status-indicator {
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9rem;
        }
        .status-connected {
            background: rgba(78, 204, 163, 0.2);
            border: 1px solid var(--success);
            color: var(--success);
        }
        .status-disconnected {
            background: rgba(255, 68, 68, 0.2);
            border: 1px solid var(--danger);
            color: var(--danger);
        }
        .meter-container {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 25px;
            margin-bottom: 25px;
        }
        @media (max-width: 1000px) {
            .meter-container { grid-template-columns: 1fr; }
        }
        .current-reading {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 25px;
            border: 1px solid var(--border);
        }
        .current-value {
            font-size: 4rem;
            font-weight: 700;
            text-align: center;
            margin: 20px 0;
            background: linear-gradient(135deg, var(--accent), var(--success));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .current-label {
            text-align: center;
            color: var(--text-secondary);
            font-size: 1.1rem;
            margin-bottom: 10px;
        }
        .current-timestamp {
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        .gauge {
            width: 100%;
            height: 20px;
            background: var(--bg-secondary);
            border-radius: 10px;
            overflow: hidden;
            margin-top: 20px;
            position: relative;
        }
        .gauge-fill {
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s ease, background 0.3s ease;
            position: relative;
        }
        .gauge-fill::after {
            content: '';
            position: absolute;
            top: 0; right: 0;
            width: 4px; height: 100%;
            background: rgba(255, 255, 255, 0.5);
            border-radius: 0 10px 10px 0;
        }
        .gauge-labels {
            display: flex;
            justify-content: space-between;
            margin-top: 5px;
            font-size: 0.75rem;
            color: var(--text-secondary);
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .stat-card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid var(--border);
        }
        .stat-card h3 {
            font-size: 0.85rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        .stat-card .value {
            font-size: 2rem;
            font-weight: 700;
        }
        .stat-card .label {
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-top: 5px;
        }
        .chart-container {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 25px;
            border: 1px solid var(--border);
            margin-bottom: 25px;
        }
        #splChart {
            width: 100%;
            height: 300px;
        }
        .data-table-container {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 25px;
            border: 1px solid var(--border);
            overflow-x: auto;
            margin-bottom: 25px;
        }
        .data-table {
            width: 100%;
            border-collapse: collapse;
        }
        .data-table th, .data-table td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }
        .data-table th {
            background: var(--bg-secondary);
            color: var(--text-secondary);
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .data-table tr:hover { background: rgba(255, 255, 255, 0.05); }
        .value-instant { color: var(--accent); font-weight: 600; }
        .value-1min { color: var(--success); font-weight: 600; }
        .value-1hr { color: #4a90e2; font-weight: 600; }
        .value-8hr { color: #9b59b6; font-weight: 600; }
        .value-peak { color: var(--warning); font-weight: 600; }
        .calibration-info {
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
            border-left: 4px solid var(--warning);
            font-size: 0.9rem;
        }
        .calibration-info h3 {
            margin-bottom: 10px;
            color: var(--warning);
            font-size: 1rem;
        }
        @media (max-width: 768px) {
            h1 { font-size: 1.8rem; }
            .current-value { font-size: 2.5rem; }
            .meter-container { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>SPL Meter</h1>
            <p class="subtitle">Real-time Sound Pressure Level Measurement</p>
        </header>
        
        <div class="status-bar">
            <div class="status-indicator status-disconnected" id="status">
                Connecting to server...
            </div>
            <div id="micInfo">Microphone: Not selected</div>
        </div>
        
        <div class="meter-container">
            <div class="current-reading">
                <div class="current-label">Current SPL</div>
                <div class="current-value" id="currentSpl">-- dB</div>
                <div class="current-timestamp" id="currentTimestamp">--:--:--</div>
                <div class="gauge">
                    <div class="gauge-fill" id="gaugeFill" style="width: 0%; background: var(--accent);"></div>
                </div>
                <div class="gauge-labels">
                    <span>0 dB</span>
                    <span>50 dB</span>
                    <span>100 dB</span>
                    <span>120 dB</span>
                </div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>Instant</h3>
                    <div class="value" id="statInstant">-- dB</div>
                    <div class="label">Real-time reading</div>
                </div>
                <div class="stat-card">
                    <h3>1 Minute Avg</h3>
                    <div class="value" id="stat1Min">-- dB</div>
                    <div class="label">Leq(1min)</div>
                </div>
                <div class="stat-card">
                    <h3>1 Hour Avg</h3>
                    <div class="value" id="stat1Hr">-- dB</div>
                    <div class="label">Leq(1hr)</div>
                </div>
                <div class="stat-card">
                    <h3>8 Hour Avg</h3>
                    <div class="value" id="stat8Hr">-- dB</div>
                    <div class="label">Leq(8hr)</div>
                </div>
                <div class="stat-card">
                    <h3>Peak (1min)</h3>
                    <div class="value" id="statPeak1Min">-- dB</div>
                    <div class="label">Max in last minute</div>
                </div>
                <div class="stat-card">
                    <h3>Peak (All)</h3>
                    <div class="value" id="statPeakAll">-- dB</div>
                    <div class="label">Maximum recorded</div>
                </div>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>SPL History (Last 5 minutes)</h2>
            <canvas id="splChart"></canvas>
        </div>
        
        <div class="data-table-container">
            <h2>Recent Readings</h2>
            <table class="data-table" id="readingsTable">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Instant (dB)</th>
                        <th>1 Min Avg (dB)</th>
                        <th>1 Hr Avg (dB)</th>
                        <th>8 Hr Avg (dB)</th>
                        <th>Peak (dB)</th>
                    </tr>
                </thead>
                <tbody id="readingsBody">
                    <tr><td colspan="6" style="text-align: center; color: var(--text-secondary);">Connecting to server...</td></tr>
                </tbody>
            </table>
        </div>
        
        <div class="calibration-info">
            <h3>ℹ️ About This Version</h3>
            <p><strong>Python Backend:</strong> All audio capture and SPL calculations are performed by the Python server using PyAudio. This provides more accurate measurements than browser-based Web Audio API.</p>
            <p><strong>Display Only:</strong> This HTML page is just a visual interface that connects to the Python server via WebSocket and displays the real-time data.</p>
            <p><strong>No Browser Permissions:</strong> Since audio is captured by Python, you don't need to grant microphone permissions to your browser.</p>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // WebSocket connection
        let socket;
        let chart;
        const chartLabels = [];
        const chartDataInstant = [];
        const chartData1Min = [];
        const chartDataPeak = [];
        const MAX_CHART_POINTS = 300;
        
        // DOM Elements
        const statusEl = document.getElementById('status');
        const micInfoEl = document.getElementById('micInfo');
        const currentSplEl = document.getElementById('currentSpl');
        const currentTimestampEl = document.getElementById('currentTimestamp');
        const gaugeFillEl = document.getElementById('gaugeFill');
        const statInstantEl = document.getElementById('statInstant');
        const stat1MinEl = document.getElementById('stat1Min');
        const stat1HrEl = document.getElementById('stat1Hr');
        const stat8HrEl = document.getElementById('stat8Hr');
        const statPeak1MinEl = document.getElementById('statPeak1Min');
        const statPeakAllEl = document.getElementById('statPeakAll');
        const readingsBodyEl = document.getElementById('readingsBody');
        
        // Connect to WebSocket
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.hostname;
            const port = parseInt(window.location.port) + 1;
            const wsUrl = `${protocol}//${host}:${port}`;
            
            console.log(`Connecting to WebSocket at ${wsUrl}`);
            
            socket = new WebSocket(wsUrl);
            
            socket.onopen = () => {
                console.log('WebSocket connected');
                statusEl.textContent = 'Connected';
                statusEl.className = 'status-indicator status-connected';
            };
            
            socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                if (data.type === 'stats') {
                    // Initial stats
                    updateStats(data);
                } else if (data.type === 'reading') {
                    // New reading
                    updateDisplay(data);
                }
            };
            
            socket.onclose = () => {
                console.log('WebSocket disconnected');
                statusEl.textContent = 'Disconnected';
                statusEl.className = 'status-indicator status-disconnected';
                // Try to reconnect
                setTimeout(connectWebSocket, 5000);
            };
            
            socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                statusEl.textContent = 'Connection Error';
                statusEl.className = 'status-indicator status-disconnected';
            };
        }
        
        // Initialize Chart
        function initChart() {
            const ctx = document.getElementById('splChart').getContext('2d');
            chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: chartLabels,
                    datasets: [
                        {
                            label: 'Instant SPL',
                            data: chartDataInstant,
                            borderColor: 'rgba(233, 69, 96, 1)',
                            backgroundColor: 'rgba(233, 69, 96, 0.1)',
                            borderWidth: 2,
                            pointRadius: 0,
                            tension: 0.1
                        },
                        {
                            label: '1 Min Average',
                            data: chartData1Min,
                            borderColor: 'rgba(78, 204, 163, 1)',
                            backgroundColor: 'rgba(78, 204, 163, 0.1)',
                            borderWidth: 2,
                            pointRadius: 0,
                            tension: 0.1
                        },
                        {
                            label: 'Peak (1min)',
                            data: chartDataPeak,
                            borderColor: 'rgba(255, 193, 7, 1)',
                            backgroundColor: 'rgba(255, 193, 7, 0.1)',
                            borderWidth: 2,
                            pointRadius: 0,
                            tension: 0.1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            min: 0,
                            max: 120,
                            title: {
                                display: true,
                                text: 'SPL (dB)'
                            },
                            ticks: { color: '#a0a0a0' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Time'
                            },
                            ticks: {
                                color: '#a0a0a0',
                                maxTicksLimit: 10
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            labels: { color: '#eaeaea' }
                        },
                        tooltip: {
                            callbacks: {
                                label: (context) => `${context.dataset.label}: ${context.raw} dB`
                            }
                        }
                    }
                }
            });
        }
        
        // Update display with new data
        function updateDisplay(data) {
            // Update timestamp
            currentTimestampEl.textContent = data.timestamp;
            
            // Update current SPL
            currentSplEl.textContent = `${data.instant} dB`;
            
            // Update gauge
            const gaugePercent = Math.min(100, Math.max(0, data.instant * 1.2));
            gaugeFillEl.style.width = `${gaugePercent}%`;
            
            // Update gauge color
            if (data.instant > 100) {
                gaugeFillEl.style.background = 'var(--danger)';
            } else if (data.instant > 80) {
                gaugeFillEl.style.background = 'var(--warning)';
            } else if (data.instant > 60) {
                gaugeFillEl.style.background = 'var(--success)';
            } else {
                gaugeFillEl.style.background = 'var(--accent)';
            }
            
            // Update stats
            updateStats(data.stats);
            
            // Update chart
            updateChart(data);
            
            // Update table
            updateTable(data);
        }
        
        function updateStats(stats) {
            statInstantEl.textContent = `${stats.instant} dB`;
            stat1MinEl.textContent = `${stats.one_min_avg} dB`;
            stat1HrEl.textContent = `${stats.one_hour_avg} dB`;
            stat8HrEl.textContent = `${stats.eight_hour_avg} dB`;
            statPeak1MinEl.textContent = `${stats.peak_1min} dB`;
            statPeakAllEl.textContent = `${stats.peak_all} dB`;
        }
        
        function updateChart(data) {
            chartLabels.push(data.timestamp);
            chartDataInstant.push(data.instant);
            chartData1Min.push(data.one_min_avg);
            chartDataPeak.push(data.peak);
            
            // Limit data points
            if (chartLabels.length > MAX_CHART_POINTS) {
                chartLabels.shift();
                chartDataInstant.shift();
                chartData1Min.shift();
                chartDataPeak.shift();
            }
            
            chart.data.labels = chartLabels;
            chart.data.datasets[0].data = chartDataInstant;
            chart.data.datasets[1].data = chartData1Min;
            chart.data.datasets[2].data = chartDataPeak;
            chart.update('none');
        }
        
        function updateTable(data) {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${data.timestamp}</td>
                <td class="value-instant">${data.instant} dB</td>
                <td class="value-1min">${data.one_min_avg} dB</td>
                <td class="value-1hr">${data.one_hour_avg} dB</td>
                <td class="value-8hr">${data.eight_hour_avg} dB</td>
                <td class="value-peak">${data.peak} dB</td>
            `;
            
            readingsBodyEl.insertBefore(row, readingsBodyEl.firstChild);
            
            // Remove old rows
            while (readingsBodyEl.children.length > 50) {
                readingsBodyEl.removeChild(readingsBodyEl.lastChild);
            }
            
            // Remove placeholder row
            const placeholder = readingsBodyEl.querySelector('tr td[colspan="6"]');
            if (placeholder) {
                placeholder.parentElement.remove();
            }
        }
        
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', () => {
            initChart();
            connectWebSocket();
        });
        
        // Clean up on page unload
        window.addEventListener('beforeunload', () => {
            if (socket) {
                socket.close();
            }
        });
    </script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(
        description='SPL Meter - Python Backend Server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python spl_meter_server.py              # Default: port 8000
  python spl_meter_server.py --port 8080 # Custom port
  python spl_meter_server.py --mic umik1  # Use UMIK-1 calibration
        """
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8000,
        help='HTTP server port (default: 8000)'
    )
    
    parser.add_argument(
        '--mic', '-m',
        type=str,
        default='default',
        choices=['umik1', 'default', 'builtin'],
        help='Microphone type for calibration (default: default)'
    )
    
    parser.add_argument(
        '--html-output',
        type=str,
        default='spl_display.html',
        help='HTML display file to generate (default: spl_display.html)'
    )
    
    args = parser.parse_args()
    
    # Generate HTML display file
    html_path = Path(args.html_output)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(HTML_DISPLAY)
    print(f"Generated display HTML: {html_path}")
    
    # Initialize SPL components
    spl_calculator = SPLCalculator(mic_type=args.mic)
    data_manager = SPLDataManager()
    
    print(f"Starting SPL Meter server on port {args.port}")
    print(f"Using {args.mic} microphone calibration")
    print(f"Open http://localhost:{args.port} in your browser")
    print("Press Ctrl+C to stop")
    print()
    
    # Start audio capture
    spl_calculator.start_audio()
    
    # Start HTTP server in a thread
    http_server = ThreadedHTTPServer(('localhost', args.port), QuietHTTPHandler)
    http_thread = threading.Thread(target=http_server.serve_forever)
    http_thread.daemon = True
    http_thread.start()
    print(f"HTTP server started on http://localhost:{args.port}")
    
    # Start WebSocket server
    asyncio.get_event_loop().run_until_complete(
        start_websocket_server(args.port, data_manager)
    )
    
    # Main audio processing loop
    try:
        while True:
            # Read audio data
            try:
                audio_data = spl_calculator.stream.read(spl_calculator.CHUNK_SIZE, exception_on_overflow=False)
                
                # Calculate SPL
                reading = spl_calculator.calculate_spl(audio_data)
                
                # Store and process reading
                data_manager.add_reading(reading['instant'], time.time())
                
                # Small delay to maintain ~10 Hz update rate
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Audio error: {e}")
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        spl_calculator.stop_audio()
        http_server.shutdown()
        print("Server stopped")


if __name__ == '__main__':
    import threading
    main()
