# 🎛️ DecibelDeck

**A zero-dependency, browser-native Professional SPL (Sound Pressure Level) Meter and Logger.**

## 📖 Overview
**DecibelDeck** is a completely client-side Single-Page Application (SPA) designed to turn any modern web browser into a highly accurate SPL meter. Built specifically with hardware like the MacBook M3 internal microphone and the **miniDSP UMIK-1** in mind, it uses the modern Web Audio API and custom `AudioWorklet` processors to perform sample-accurate, real-time acoustic energy calculations without dropping frames. 

Because it operates entirely in the browser, there is zero installation required, no backend server needed, and complete data privacy.

## ✨ Key Features
* **Zero-Setup & Portable:** A single `.html` file. No `npm install`, no dependencies, no databases. 
* **Sample-Accurate Processing:** Uses `AudioWorklet` to analyze raw audio data at the sample level (e.g., 48kHz) bypassing the browser's main thread to prevent lag.
* **Smart UMIK-1 Auto-Calibration:** Upload your UMIK-1 `.txt` or `.cal` file. The app instantly extracts the `Sens Factor`, extracts your serial number, and applies the perfect mathematical offset for true dB SPL.
* **Rolling Time Windows:** Instant (~100ms), 1-Minute, 1-Hour, and 8-Hour rolling Leq (average) and Peak metrics.
* **Paginated Real-Time Log:** A built-in dashboard recording your SPL second-by-second with auto-tailing.
* **Data Export & Cloud Hooks:** Instantly download up to 8 hours of data as a perfectly formatted `.CSV`, or push it in real-time to Google Sheets, Slack, or Make.com via Webhooks.
* **Themeable & Responsive:** Fully responsive CSS with auto-detecting Light/Dark modes.

---

## 🚀 Setup & Run Instructions

Because this app utilizes a clever "Data URI" encoding trick for its `AudioWorklet`, it bypasses standard Chrome local-file security restrictions. 

### Method 1: The Zero-Setup Way (Easiest)
1. Download the `spl-meter.html` file.
2. Double-click the file to open it in Google Chrome, Edge, or Safari.
3. Grant Microphone permissions when prompted.
4. Start measuring!

### Method 2: Local Web Server (Recommended for developers)
If you want to modify the code or if your specific browser restricts `file:///` microphone access:
1. Open your terminal and navigate to the folder containing the file.
2. Run a simple Python server (built into Mac/Linux):
   ```bash
   python3 -m http.server 8000
   ```
3. Open your browser and navigate to `http://localhost:8000/spl-meter.html`

---

## 💾 Storage & Data Footprint

Because DecibelDeck logs acoustic data every single second, understanding file sizes is important for long-term logging. A single CSV row uses roughly **70 Bytes** of data. 

Here are the storage estimations for the exported `.CSV` file over various time periods:

| Time Period | Data Points (Rows) | Est. CSV File Size | RAM Impact (Browser) |
| :--- | :--- | :--- | :--- |
| **1 Second** | 1 | ~70 Bytes | Negligible |
| **1 Minute** | 60 | ~4.2 KB | Negligible |
| **1 Hour** | 3,600 | ~252 KB | Negligible |
| **8 Hours** | 28,800 | ~2.0 MB | ~5 MB (Current Cap) |
| **1 Day** (24h) | 86,400 | ~6.0 MB | *Requires Roadmap Update* |
| **1 Week** | 604,800 | ~42.3 MB | *Requires Roadmap Update* |
| **1 Month** | 2,592,000 | ~181.4 MB | *Requires Roadmap Update* |

*(Note: The current application artificially caps RAM storage at 8 hours / 28,800 rows to guarantee browser stability. Logs pushed via Webhook API bypass this limitation).*

---

## ⚖️ Benefits vs. Drawbacks (Current Version)

### 🟢 Benefits
* **Absolute Privacy:** Audio streams are processed locally in your RAM and instantly discarded. Nothing is ever recorded or sent over the internet (unless you explicitly set up a Webhook).
* **High Portability:** Put the HTML file on a USB drive or email it to yourself. It works instantly on any machine with a modern browser.
* **No "Environment" Rot:** Because there are no Node modules or dependencies, this app won't "break" 5 years from now due to outdated packages.
* **Incredibly Lightweight:** A fully loaded 8-hour log exports as a tiny ~2 MB CSV file, making it easy to email or open in Excel.

### 🔴 Drawbacks
1. **Memory Ceiling:** The app currently stores 1-second logs in an array in the browser's RAM, artificially capped at 8 hours to prevent browser crashing.
2. **Tab Throttling:** Modern browsers aggressively throttle JavaScript in tabs that run in the background or get minimized. While active `AudioContext` usually prevents this, prolonged minimization can cause dropped seconds in the rolling averages.
3. **Webhook CORS Restrictions:** Sending data to some APIs directly from a browser is blocked by "Cross-Origin Resource Sharing" (CORS) policies.
4. **Lack of Weighting:** Currently measures raw Z-weighting (unweighted) acoustic energy. A-weighting and C-weighting are not yet implemented.

---

## 🗺️ Roadmap & Solutions

Here is the roadmap for addressing the current drawbacks and expanding functionality:

### Phase 1: Overcoming Browser Limitations (Long-term Logging)
* **Solution to Memory Limit (IndexedDB):** Transition the history array to the browser's native `IndexedDB`. This will allow the app to securely log the **181+ MB** needed for continuous 1-month recordings locally without consuming active RAM, persisting data even if the tab is accidentally closed.
* **Solution to Tab Throttling (Web Workers/Wake Lock API):** Implement the Screen Wake Lock API (`navigator.wakeLock.request('screen')`) to keep the display active, and move the 1-second interval loop directly into a dedicated Web Worker to ensure background timing remains flawless.

### Phase 2: Advanced Acoustics
* **A/C Weighting Implementation:** Build DSP (Digital Signal Processing) biquad filters directly into the `AudioWorklet`. Users will be able to toggle between dB(Z), dB(A), and dB(C) dynamically.
* **Frequency Analyzer:** Add an HTML5 Canvas-based real-time RTA (Real-Time Analyzer) to visualize the frequency spectrum alongside the SPL readings.

### Phase 3: Cloud & Export Resilience
* **CORS Proxy / Backend-BFF:** Provide an optional, lightweight Docker container (Node.js/Express) that acts as a "Backend For Frontend" (BFF) to safely route Webhook data to strict APIs without triggering browser CORS errors.
* **Auto-Save functionality:** Periodically generate and save the CSV to the local downloads folder automatically every hour to prevent data loss on massive multi-day recording runs. 

---

## 📜 License
MIT License - Feel free to modify, distribute, and use this for personal or professional acoustic measurements.
