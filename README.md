# SPL Meter

> **Real-time Sound Pressure Level Measurement Web App**

A single-page web application for measuring sound pressure levels (SPL) in real-time using your device's microphone. Supports both built-in microphones and professional USB measurement microphones like the **UMIK-1**.

[License: MIT](https://opensource.org/licenses/MIT)  
[HTML5](https://html5.org/)  
[JavaScript](https://javascript.info/)  
[Chart.js](https://www.chartjs.org/)

---

## 📋 Overview

SPL Meter is a browser-based sound level meter that provides real-time sound pressure level measurements. It's designed for:

- **Audio engineers** testing equipment and environments
- **Health & safety** monitoring workplace noise levels
- **Environmental** sound level tracking
- **DIY acoustics** enthusiasts and hobbyists
- **Educational** purposes and demonstrations

The application uses the **Web Audio API** to capture microphone input and calculate SPL values in real-time. It supports time-weighted averages (Leq) across multiple intervals and tracks peak levels.

---

## ✨ Features

### 🎯 Core Measurement

- ✅ **Real-time SPL measurement** with 100ms update intervals
- ✅ **Instant readings** - Current SPL value
- ✅ **Time-weighted averages (Leq)**
  - 1-minute average
  - 1-hour average
  - 8-hour average
- ✅ **Peak level tracking**
  - 1-minute peak
  - All-time peak
- ✅ **A-weighting approximation** for human-hearing response

### 🎛️ User Interface

- ✅ **Interactive gauge** with color-coded levels
  - Green: < 60 dB (Quiet)
  - Yellow: 60-80 dB (Moderate)
  - Red: > 100 dB (Loud)
- ✅ **Real-time chart** showing last 5 minutes of data
- ✅ **Data table** with timestamps and all readings
- ✅ **Statistics cards** for quick reference
- ✅ **Responsive design** - Works on desktop and mobile

### 🔊 Microphone Support

- ✅ **Automatic device detection** - Lists all available microphones
- ✅ **UMIK-1 support** with calibration offset
- ✅ **Built-in microphone** support (MacBook, etc.)
- ✅ **USB microphone** compatibility
- ✅ **Device selection** dropdown with visual indicators

### 📊 Data & Visualization

- ✅ **Chart.js integration** for interactive graphs
- ✅ **Multiple data series** (Instant, 1-min avg, Peak)
- ✅ **Time-based x-axis** with proper scaling
- ✅ **Color-coded readings** in data table
- ✅ **Historical data** display (last 50 readings)

### ⚙️ Technical

- ✅ **Web Audio API** for audio processing
- ✅ **No server required** - Pure client-side application
- ✅ **No dependencies** (except Chart.js CDN)
- ✅ **Clean resource management** - Proper audio context cleanup
- ✅ **Error handling** for microphone access

---

## 🚀 Quick Start

### Option 1: Direct Use

1. Open `index.html` in a modern browser (Chrome, Edge, Safari, Firefox)
2. Select your microphone from the dropdown
3. Click "Start Measurement"
4. Grant microphone permissions when prompted
5. View real-time SPL readings!

### Option 2: Local Server

```bash
# Using Python
python -m http.server 8000

# Using Node.js
npx serve

# Using PHP
php -S localhost:8000
```

Then open `http://localhost:8000` in your browser.

### Option 3: Deploy to Web Server

Simply upload all files to your web server. No server-side processing required.

---

## 📊 Usage

### Basic Operation

1. **Select Microphone**: Choose your input device from the dropdown
  - UMIK-1 will be automatically detected and labeled
  - Built-in microphones are also supported
2. **Start Measurement**: Click the "Start" button
  - The app will request microphone permissions
  - Once granted, measurements begin immediately
3. **View Readings**:
  - **Current SPL**: Large display showing instant reading
  - **Gauge**: Visual representation of current level
  - **Stats Cards**: Instant, 1-min, 1-hr, 8-hr averages and peaks
  - **Chart**: Historical trend (last 5 minutes)
  - **Table**: Detailed readings with timestamps
4. **Stop Measurement**: Click "Stop" to pause data collection

### Understanding the Readings


| Metric              | Description                         | Typical Use Case        |
| ------------------- | ----------------------------------- | ----------------------- |
| **Instant**         | Current SPL at this moment          | Real-time monitoring    |
| **1-min Avg (Leq)** | Energy-averaged level over 1 minute | Short-term exposure     |
| **1-hr Avg (Leq)**  | Energy-averaged level over 1 hour   | Workplace monitoring    |
| **8-hr Avg (Leq)**  | Energy-averaged level over 8 hours  | Occupational safety     |
| **Peak (1-min)**    | Maximum level in last minute        | Impact noise            |
| **Peak (All)**      | Maximum level since start           | Absolute peak detection |


**Leq (Equivalent Continuous Sound Level)**: The steady sound level that would contain the same acoustic energy as the varying levels over the measurement period.

---

## 🎯 Calibration

### UMIK-1

The UMIK-1 is a calibrated measurement microphone with the following specifications:

- **Sensitivity**: -34 dBFS at 94 dB SPL (1 kHz)
- **Frequency Response**: 20 Hz - 20 kHz ±1 dB
- **Dynamic Range**: 26 dB - 140 dB SPL

This app applies an offset of **+128 dB** to convert digital dBFS to SPL for the UMIK-1.

> ⚠️ **For Professional Use**: For absolute accuracy, apply the UMIK-1's individual calibration file. Each UMIK-1 comes with a unique calibration certificate that should be used for precise measurements.

### Built-in Microphones

Built-in microphones (MacBook, laptop, etc.) are **not calibrated** for SPL measurement:

- Readings are **relative**, not absolute
- Useful for **comparative measurements** and trends
- Not suitable for **legal or compliance** purposes

The app applies an approximate offset of **+94 dB** for standard microphones.

---

## 📈 Roadmap

### 🔜 v1.1 (Planned)

- **C-weighting option** (flat frequency response)
- **Z-weighting option** (no weighting)
- **Export data** to CSV/JSON
- **Dark/Light theme toggle**
- **Custom calibration offsets** for different microphones
- **Threshold alerts** (visual/audio warnings)
- **Mobile browser optimization**

### 🎯 v1.2 (Future)

- **Frequency analysis** (1/3 octave bands)
- **Spectrogram view**
- **Data logging** with timestamps to file
- **Multiple microphone support** (simultaneous)
- **OSHA/ISO compliance modes**
- **Printable reports**
- **PWA support** (Install as app)

### 🚀 v2.0 (Long-term)

- **UMIK-1 calibration file import** (for absolute accuracy)
- **Real-time noise dose calculation**
- **Multi-channel measurement**
- **Cloud sync** for remote monitoring
- **API for integration** with other systems
- **Machine learning** for sound classification
- **Offline mode** with local storage

---

## 🛠️ Technical Details

### Architecture

```
┌─────────────────────────────────────────────────┐
│                    Browser                         │
├─────────────────────────────────────────────────┤
│  User Interface (HTML/CSS/JS)                     │
│  ┌─────────────┐    ┌─────────────────────────┐  │
│  │   Chart.js  │    │   Web Audio API          │  │
│  │   Visuals   │    │   ┌─────────────────┐   │  │
│  └─────────────┘    │   │ AudioContext    │   │  │
│                     │   │ AnalyserNode     │   │  │
│                     │   │ MediaStream      │   │  │
│                     │   └─────────────────┘   │  │
│                     └─────────────────────────┘  │
│  ┌─────────────────────────────────────────────┐│
│  │  SPL Calculation Engine                        ││
│  │  - RMS calculation                             ││
│  │  - dB conversion                               ││
│  │  - A-weighting                                 ││
│  │  - Time-weighted averages                      ││
│  │  - Peak tracking                               ││
│  └─────────────────────────────────────────────┘│
└─────────────────────────────────────────────────┘
```

### SPL Calculation

1. **Capture Audio**: Microphone → MediaStream → AudioContext
2. **Get Time Domain Data**: `analyser.getByteTimeDomainData()`
3. **Convert to Float**: Normalize to -1.0 to 1.0 range
4. **Calculate RMS**: `sqrt(mean(samples²))`
5. **Convert to dBFS**: `20 * log10(RMS)`
6. **Apply Calibration Offset**: `dBFS + offset` (128 for UMIK-1, 94 for default)
7. **Apply A-weighting**: Frequency-dependent correction (approximated)
8. **Calculate Averages**: Energy-based Leq calculation for each time window

### Performance

- **Update Rate**: 100ms (10 readings per second)
- **FFT Size**: 2048 samples
- **Memory Usage**: Circular buffers for efficient data management
- **CPU Usage**: Optimized with requestAnimationFrame

---

## 📦 File Structure

```
spl-meter/
├── index.html          # Main application file
├── README.md           # This file
├── LICENSE             # MIT License
└── assets/             # (Optional) Static assets
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Development Setup

```bash
# Clone the repository
git clone https://github.com/your-username/spl-meter.git
cd spl-meter

# Open index.html in your browser
# No build step required!
```

### Testing

- Test in multiple browsers (Chrome, Firefox, Safari, Edge)
- Test with different microphone types
- Verify calculations with known sound sources

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Web Audio API** - For real-time audio processing in the browser
- **Chart.js** - For beautiful, interactive data visualization
- **UMIK-1** - MiniDSP's affordable measurement microphone
- **All contributors** - For their valuable input and testing

---

## 📞 Support

- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Join the conversation in GitHub Discussions
- **Documentation**: Check the README and in-app help

---

## 🏷️ Metadata

- **Version**: 1.0.0
- **Author**: Transparency-X
- **Maintainer**: Transparency-X
- **Homepage**: [https://github.com/transparency-x/spl-meter](https://github.com/transparency-x/spl-meter)
- **Keywords**: SPL, sound, audio, measurement, microphone, UMIK-1, dB, decibel, noise, acoustics

---

*Built with ❤️ for the audio community*
