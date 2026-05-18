#!/usr/bin/env python3
"""
SPL Meter HTML Generator
=======================

A Python script to generate and serve the SPL Meter web app locally.
This script creates the complete HTML file and optionally starts a local server.

Usage:
    python generate_spl_meter.py [--serve] [--port PORT] [--output FILE]

Options:
    --serve     Start a local HTTP server after generating the file
    --port PORT Specify the port for the server (default: 8000)
    --output FILE  Specify output filename (default: spl_meter.html)
"""

import os
import sys
import argparse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SPL Meter - Real-time Sound Level Measurement</title>
    <style>
        \:root {
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

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            margin-bottom: 30px;
        }

        h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(135deg, var(--accent), var(--success));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .subtitle {
            color: var(--text-secondary);
            font-size: 1.1rem;
        }

        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 25px;
            flex-wrap: wrap;
            align-items: center;
        }

        .control-group {
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }

        select, button {
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        select {
            background: var(--bg-card);
            color: var(--text-primary);
            border: 1px solid var(--border);
            min-width: 250px;
        }

        select\:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 2px var(--accent-glow);
        }

        button {
            background: var(--bg-card);
            color: var(--text-primary);
            border: 1px solid var(--border);
            font-weight: 600;
        }

        button\:hover {
            background: var(--accent);
            border-color: var(--accent);
            transform: translateY(-2px);
        }

        button\:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        button.stop {
            background: var(--danger);
            border-color: var(--danger);
        }

        button.stop\:hover {
            background: #ff6666;
            border-color: #ff6666;
        }

        .status {
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 600;
            margin-left: auto;
        }

        .status.connected {
            background: rgba(78, 204, 163, 0.2);
            border: 1px solid var(--success);
            color: var(--success);
        }

        .status.disconnected {
            background: rgba(255, 68, 68, 0.2);
            border: 1px solid var(--danger);
            color: var(--danger);
        }

        .status.error {
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
            .meter-container {
                grid-template-columns: 1fr;
            }
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
            transition: width 0.3s ease;
            position: relative;
        }

        .gauge-fill::after {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 4px;
            height: 100%;
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

        .data-table-container {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 25px;
            border: 1px solid var(--border);
            overflow-x: auto;
        }

        .data-table {
            width: 100%;
            border-collapse: collapse;
        }

        .data-table th,
        .data-table td {
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

        .data-table tr\:hover {
            background: rgba(255, 255, 255, 0.05);
        }

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

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
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

        .info-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }

        .badge-umik {
            background: rgba(155, 89, 182, 0.2);
            border: 1px solid #9b59b6;
            color: #9b59b6;
        }

        .badge-builtin {
            background: rgba(74, 144, 226, 0.2);
            border: 1px solid #4a90e2;
            color: #4a90e2;
        }

        @media (max-width: 768px) {
            h1 { font-size: 1.8rem; }
            .current-value { font-size: 2.5rem; }
            .controls { flex-direction: column; align-items: stretch; }
            .control-group { flex-direction: column; align-items: stretch; }
            select { width: 100%; }
            .status { margin-left: 0; text-align: center; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>SPL Meter</h1>
            <p class="subtitle">Real-time Sound Pressure Level Measurement</p>
        </header>

        <div class="controls">
            <div class="control-group">
                <select id="micSelect">
                    <option value="">Select Microphone...</option>
                </select>
                <button id="startBtn">Start Measurement</button>
                <button id="stopBtn" class="stop" disabled>Stop Measurement</button>
            </div>
            <div class="status disconnected" id="status">Disconnected</div>
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
                    <tr><td colspan="6" style="text-align: center; color: var(--text-secondary);">No data yet. Start measurement to see readings.</td></tr>
                </tbody>
            </table>
        </div>

        <div class="calibration-info">
            <h3>⚠️ Calibration Notice</h3>
            <p><strong>UMIK-1:</strong> For accurate measurements with the UMIK-1, ensure it's selected as the input device. The UMIK-1 has a flat frequency response and comes with calibration data. This app uses a standard reference; for professional use, apply the UMIK-1's calibration file.</p>
            <p><strong>Built-in Mic:</strong> MacBook microphones are not calibrated for SPL measurement. Readings will be relative and may not reflect true acoustic SPL values.</p>
            <p><strong>Reference:</strong> This meter uses 20 μPa (0 dB SPL = 0.00002 Pa) as the reference pressure.</p>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        const CONFIG = {
            fftSize: 2048,
            smoothingTimeConstant: 0.8,
            updateInterval: 100,
            maxHistory: 300,
            maxChartPoints: 300,
            calibration: {
                umik1: { offset: 128, label: 'UMIK-1' },
                default: { offset: 94, label: 'Default' }
            }
        };

        let audioContext;
        let analyser;
        let microphone;
        let mediaStream;
        let rafId;
        let chart;
        let chartLabels = [];
        let chartDataInstant = [];
        let chartData1Min = [];
        let chartDataPeak = [];

        const readings = [];
        const oneMinReadings = [];
        const oneHourReadings = [];
        const eightHourReadings = [];

        let peak1Min = -Infinity;
        let peakAll = -Infinity;
        let peak1MinResetTime = null;

        const micSelect = document.getElementById('micSelect');
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const statusEl = document.getElementById('status');
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

        async function init() {
            try {
                await loadMicrophones();
                initChart();
                setupEventListeners();
                console.log('SPL Meter initialized successfully');
            } catch (err) {
                console.error('Initialization error:', err);
                statusEl.textContent = 'Initialization Error';
                statusEl.className = 'status error';
            }
        }

        async function loadMicrophones() {
            try {
                const devices = await navigator.mediaDevices.enumerateDevices();
                const mics = devices.filter(d => d.kind === 'audioinput');

                micSelect.innerHTML = '<option value="">Select Microphone...</option>';

                if (mics.length === 0) {
                    const option = document.createElement('option');
                    option.value = '';
                    option.textContent = 'No microphones found';
                    option.disabled = true;
                    micSelect.appendChild(option);
                    return;
                }

                mics.forEach(mic => {
                    const option = document.createElement('option');
                    option.value = mic.deviceId;
                    option.textContent = mic.label || `Microphone ${micSelect.length + 1}`;

                    if (mic.label && mic.label.toLowerCase().includes('umik')) {
                        option.innerHTML = `${mic.label} <span class="info-badge badge-umik">UMIK</span>`;
                    } else if (mic.label && (mic.label.toLowerCase().includes('builtin') || mic.label.toLowerCase().includes('macbook'))) {
                        option.innerHTML = `${mic.label} <span class="info-badge badge-builtin">Built-in</span>`;
                    }

                    micSelect.appendChild(option);
                });

                micSelect.disabled = false;
            } catch (err) {
                console.error('Error loading microphones:', err);
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'Error loading microphones';
                option.disabled = true;
                micSelect.appendChild(option);
                throw err;
            }
        }

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
                    interaction: { intersect: false, mode: 'index' },
                    scales: {
                        y: {
                            beginAtZero: true,
                            min: 0,
                            max: 120,
                            title: { display: true, text: 'SPL (dB)' },
                            ticks: { color: '#a0a0a0' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        },
                        x: {
                            title: { display: true, text: 'Time' },
                            ticks: { color: '#a0a0a0', maxTicksLimit: 10 },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        }
                    },
                    plugins: {
                        legend: { labels: { color: '#eaeaea' } },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `${context.dataset.label}: ${context.raw} dB`;
                                }
                            }
                        }
                    }
                }
            });
        }

        function setupEventListeners() {
            startBtn.addEventListener('click', startMeasurement);
            stopBtn.addEventListener('click', stopMeasurement);
        }

        async function startMeasurement() {
            if (!micSelect.value) {
                alert('Please select a microphone first.');
                return;
            }

            try {
                stopMeasurement();

                audioContext = new (window.AudioContext || window.webkitAudioContext)();

                mediaStream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        deviceId: { exact: micSelect.value },
                        echoCancellation: false,
                        noiseSuppression: false,
                        autoGainControl: false
                    }
                });

                analyser = audioContext.createAnalyser();
                analyser.fftSize = CONFIG.fftSize;
                analyser.smoothingTimeConstant = CONFIG.smoothingTimeConstant;

                microphone = audioContext.createMediaStreamSource(mediaStream);
                microphone.connect(analyser);

                startProcessing();

                startBtn.disabled = true;
                stopBtn.disabled = false;
                statusEl.textContent = 'Measuring...';
                statusEl.className = 'status connected';

                console.log('Measurement started successfully');
            } catch (err) {
                console.error('Error starting measurement:', err);
                statusEl.textContent = `Error: ${err.message}`;
                statusEl.className = 'status error';
                startBtn.disabled = false;
                stopBtn.disabled = true;

                let errorMsg = 'Error starting measurement';
                if (err.name === 'NotAllowedError') {
                    errorMsg = 'Microphone access denied. Please grant microphone permissions.';
                } else if (err.name === 'NotFoundError') {
                    errorMsg = 'No microphone found. Please connect a microphone.';
                } else if (err.message.includes('deviceId')) {
                    errorMsg = 'Selected microphone not available. Please try another.';
                }
                alert(errorMsg);
            }
        }

        function stopMeasurement() {
            if (rafId) {
                cancelAnimationFrame(rafId);
                rafId = null;
            }

            if (mediaStream) {
                mediaStream.getTracks().forEach(track => {
                    try { track.stop(); } catch (e) { console.warn('Error stopping track:', e); }
                });
                mediaStream = null;
            }

            if (audioContext) {
                audioContext.close().catch(e => { console.warn('Error closing audio context:', e); });
                audioContext = null;
            }

            startBtn.disabled = false;
            stopBtn.disabled = true;
            statusEl.textContent = 'Stopped';
            statusEl.className = 'status disconnected';
            console.log('Measurement stopped');
        }

        function startProcessing() {
            const timeDomainData = new Uint8Array(analyser.frequencyBinCount);
            let lastUpdate = 0;

            function processFrame(timestamp) {
                if (!audioContext || audioContext.state === 'closed') return;

                try {
                    analyser.getByteTimeDomainData(timeDomainData);
                    const spl = calculateSPL(timeDomainData);
                    const now = new Date();

                    if (timestamp - lastUpdate >= CONFIG.updateInterval) {
                        updateReadings(spl, now);
                        lastUpdate = timestamp;
                    }

                    rafId = requestAnimationFrame(processFrame);
                } catch (err) {
                    console.error('Error in processFrame:', err);
                    stopMeasurement();
                    statusEl.textContent = 'Error processing audio';
                    statusEl.className = 'status error';
                    startBtn.disabled = false;
                }
            }

            rafId = requestAnimationFrame(processFrame);
        }

        function calculateSPL(timeDomainData) {
            const floatData = new Float32Array(timeDomainData.length);
            for (let i = 0; i < timeDomainData.length; i++) {
                floatData[i] = (timeDomainData[i] - 128) / 128.0;
            }

            let sumSquares = 0;
            for (let i = 0; i < floatData.length; i++) {
                sumSquares += floatData[i] * floatData[i];
            }
            const meanSquares = sumSquares / floatData.length;
            const rms = Math.sqrt(meanSquares);

            let dbfs;
            if (rms > 0) {
                dbfs = 20 * Math.log10(rms);
            } else {
                dbfs = -Infinity;
            }

            const selectedMic = micSelect.options[micSelect.selectedIndex];
            const isUmik = selectedMic && selectedMic.textContent.toLowerCase().includes('umik');
            const calibrationOffset = isUmik ? CONFIG.calibration.umik1.offset : CONFIG.calibration.default.offset;
            let spl = dbfs + calibrationOffset;
            spl = Math.max(0, Math.min(140, spl));
            spl = applyAWeighting(spl);
            return Math.round(spl * 10) / 10;
        }

        function applyAWeighting(spl) {
            return spl - 2;
        }

        function updateReadings(spl, timestamp) {
            const reading = {
                timestamp: timestamp,
                instant: spl,
                oneMinAvg: null,
                oneHrAvg: null,
                eightHrAvg: null,
                peak: spl
            };

            readings.push(reading);
            oneMinReadings.push(reading);
            oneHourReadings.push(reading);
            eightHourReadings.push(reading);

            const oneMinAgo = new Date(timestamp.getTime() - 60 * 1000);
            const oneHrAgo = new Date(timestamp.getTime() - 60 * 60 * 1000);
            const eightHrAgo = new Date(timestamp.getTime() - 8 * 60 * 60 * 1000);

            const oneMinIndex = oneMinReadings.findIndex(r => r.timestamp >= oneMinAgo);
            if (oneMinIndex > 0) oneMinReadings.splice(0, oneMinIndex);

            if (readings.length % 10 === 0) {
                const oneHrIndex = oneHourReadings.findIndex(r => r.timestamp >= oneHrAgo);
                if (oneHrIndex > 0) oneHourReadings.splice(0, oneHrIndex);
            }

            if (readings.length % 60 === 0) {
                const eightHrIndex = eightHourReadings.findIndex(r => r.timestamp >= eightHrAgo);
                if (eightHrIndex > 0) eightHourReadings.splice(0, eightHrIndex);
            }

            reading.oneMinAvg = calculateLeq(oneMinReadings);
            reading.oneHrAvg = calculateLeq(oneHourReadings);
            reading.eightHrAvg = calculateLeq(eightHourReadings);

            if (!peak1MinResetTime || timestamp >= peak1MinResetTime) {
                if (!peak1MinResetTime || timestamp >= new Date(peak1MinResetTime.getTime() + 60 * 1000)) {
                    peak1Min = spl;
                    peak1MinResetTime = timestamp;
                } else {
                    peak1Min = Math.max(peak1Min, spl);
                }
            } else {
                peak1Min = Math.max(peak1Min, spl);
            }
            peakAll = Math.max(peakAll, spl);

            reading.oneMinAvg = Math.round(reading.oneMinAvg * 10) / 10;
            reading.oneHrAvg = Math.round(reading.oneHrAvg * 10) / 10;
            reading.eightHrAvg = Math.round(reading.eightHrAvg * 10) / 10;
            reading.peak = Math.round(peak1Min * 10) / 10;

            if (readings.length > CONFIG.maxHistory) readings.shift();
            updateUI(reading);
            updateChart(reading);
        }

        function calculateLeq(readingsArray) {
            if (readingsArray.length === 0) return 0;
            let sumEnergy = 0;
            for (const r of readingsArray) {
                sumEnergy += Math.pow(10, r.instant / 10);
            }
            const avgEnergy = sumEnergy / readingsArray.length;
            const leq = 10 * Math.log10(avgEnergy);
            return isFinite(leq) ? leq : 0;
        }

        function updateUI(reading) {
            const timeStr = reading.timestamp.toLocaleTimeString('en-GB', {
                hour: '2-digit', minute: '2-digit', second: '2-digit'
            });

            currentSplEl.textContent = `${reading.instant} dB`;
            currentTimestampEl.textContent = timeStr;

            const gaugePercent = Math.min(100, Math.max(0, reading.instant * 1.2));
            gaugeFillEl.style.width = `${gaugePercent}%`;

            if (reading.instant > 100) {
                gaugeFillEl.style.background = 'var(--danger)';
            } else if (reading.instant > 80) {
                gaugeFillEl.style.background = 'var(--warning)';
            } else if (reading.instant > 60) {
                gaugeFillEl.style.background = 'var(--success)';
            } else {
                gaugeFillEl.style.background = 'var(--accent)';
            }

            statInstantEl.textContent = `${reading.instant} dB`;
            stat1MinEl.textContent = `${reading.oneMinAvg} dB`;
            stat1HrEl.textContent = `${reading.oneHrAvg} dB`;
            stat8HrEl.textContent = `${reading.eightHrAvg} dB`;
            statPeak1MinEl.textContent = `${Math.round(peak1Min * 10) / 10} dB`;
            statPeakAllEl.textContent = `${Math.round(peakAll * 10) / 10} dB`;

            updateTable(reading, timeStr);
        }

        function updateTable(reading, timeStr) {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${timeStr}</td>
                <td class="value-instant">${reading.instant} dB</td>
                <td class="value-1min">${reading.oneMinAvg} dB</td>
                <td class="value-1hr">${reading.oneHrAvg} dB</td>
                <td class="value-8hr">${reading.eightHrAvg} dB</td>
                <td class="value-peak">${reading.peak} dB</td>
            `;

            readingsBodyEl.insertBefore(row, readingsBodyEl.firstChild);
            while (readingsBodyEl.children.length > 50) {
                readingsBodyEl.removeChild(readingsBodyEl.lastChild);
            }

            const noDataRow = readingsBodyEl.querySelector('tr td[colspan="6"]');
            if (noDataRow) noDataRow.parentElement.remove();
        }

        function updateChart(reading) {
            const timeStr = reading.timestamp.toLocaleTimeString('en-GB', {
                hour: '2-digit', minute: '2-digit', second: '2-digit'
            });

            chartLabels.push(timeStr);
            chartDataInstant.push(reading.instant);
            chartData1Min.push(reading.oneMinAvg);
            chartDataPeak.push(peak1Min);

            const maxPoints = CONFIG.maxChartPoints;
            if (chartLabels.length > maxPoints) {
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

        document.addEventListener('DOMContentLoaded', init);
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && !stopBtn.disabled) {}
        });
        window.addEventListener('beforeunload', () => { stopMeasurement(); });
    </script>
</body>
</html>'''

def generate_html(output_file: str = "spl_meter.html") -> Path:
    """
    Generate the SPL Meter HTML file.

    Args:
        output_file: Path to save the HTML file

    Returns:
        Path to the generated file
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(HTML_TEMPLATE)

    return output_path

class QuietHandler(SimpleHTTPRequestHandler):
    """HTTP request handler that doesn't log requests."""
    def log_message(self, format, *args):
        pass

def serve_html(port: int = 8000, directory: str = "."):
    """
    Start a local HTTP server to serve the generated HTML file.

    Args:
        port: Port to serve on
        directory: Directory to serve from
    """
    os.chdir(directory)

    server_address = ('', port)
    httpd = HTTPServer(server_address, QuietHandler)

    print(f"\n{'='*60}")
    print(f"SPL Meter is now running locally!")
    print(f"{'='*60}")
    print(f"URL: http://localhost:{port}/spl_meter.html")
    print(f"{'='*60}")
    print("Press Ctrl+C to stop the server\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        httpd.server_close()

def main():
    parser = argparse.ArgumentParser(
        description='Generate and optionally serve the SPL Meter web app locally.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_spl_meter.py                     # Generate HTML file
  python generate_spl_meter.py --serve            # Generate and serve
  python generate_spl_meter.py --port 8080        # Serve on port 8080
  python generate_spl_meter.py --output my_app.html  # Custom filename
        """
    )

    parser.add_argument('--serve', '-s', action='store_true',
                        help='Start a local HTTP server after generating the file')
    parser.add_argument('--port', '-p', type=int, default=8000,
                        help='Port for the HTTP server (default: 8000)')
    parser.add_argument('--output', '-o', type=str, default='spl_meter.html',
                        help='Output HTML filename (default: spl_meter.html)')

    args = parser.parse_args()

    print(f"Generating SPL Meter HTML file: {args.output}")
    output_path = generate_html(args.output)
    print(f"✓ File generated: {output_path.absolute()}")

    if args.serve:
        serve_html(port=args.port)
    else:
        print(f"\nTo view the app:")
        print(f"  1. Open {output_path.absolute()} in your browser")
        print(f"  2. Or run: python {__file__} --serve")

if __name__ == '__main__':
    main()
