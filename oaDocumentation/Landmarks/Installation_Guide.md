# ⚙️ OPEN-AIR Installation Guide

This guide provides detailed instructions for setting up the OPEN-AIR platform on your local machine.

## Quick Start
Follow these steps to get OPEN-AIR running:

1. **Clone the Repository:**
```bash
git clone https://github.com/LikeDotAudio/OPEN-AIR
cd OPEN-AIR
```

2. **Set up Virtual Environment:**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install Dependencies:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 📦 Project Dependencies
For a detailed breakdown of every package used, refer to [Installation/dependancy/Dependancies.md](https://github.com/LikeDotAudio/OPEN-AIR/blob/main/Installation/dependancy/Dependancies.md).

### 🔬 Data Science & Mathematical Computation
*   **numpy**: Numerical computing, essential for processing high-speed spectral data and audio buffers.
*   **pandas**: Data manipulation tool used for analyzing and organizing structured datasets.

### 📊 Visualization & Rendering
*   **matplotlib**: Creating static, animated, and interactive visualizations (spectrograms, waveforms, data plots).
*   **Pillow (PIL)**: Image processing, required for Matplotlib and Tkinter image support.

### 🎛️ Instrument Control & Hardware Protocols
*   **pyvisa**: Virtual Instrument Software Architecture (VISA) API for controlling measurement equipment.
*   **pyusb**: Direct USB interface for hardware not using standard protocols.
*   **python-usbtmc**: USB Test & Measurement Class for direct control of USB-connected test equipment.
*   **python-vxi11**: VXI-11 protocol for controlling LXI compatible instruments over Ethernet.
*   **pyserial**: Communication through serial ports (RS-232, USB-to-Serial).

### 🌐 Networking & IoT Messaging
*   **zeroconf**: Multicast DNS (mDNS) service discovery for finding instruments automatically.
*   **scapy**: Network packet manipulation tool for scanning, mapping, and debugging.
*   **paho-mqtt**: Synchronous MQTT client for publish-subscribe messaging.
*   **aiomqtt**: Asynchronous MQTT client for non-blocking network messaging.
*   **python-osc**: Open Sound Control (OSC) protocol for real-time control data sharing.

### 🎹 Audio & MIDI Integration
*   **mido**: Working with MIDI messages and ports.
*   **python-rtmidi**: Fast, cross-platform backend for real-time MIDI I/O.

### 📄 Document Parsing & Extraction
*   **pdfplumber**: Extracting text, tables, and data from PDF files.
*   **beautifulsoup4 (bs4)**: Parsing HTML and XML documents for web scraping or instrument web interfaces.

### 🛠️ System Utilities & Performance
*   **psutil**: Retrieving process and system utilization info (CPU, memory, disks, network).
*   **orjson**: Ultra-fast JSON parsing library for configurations and network payloads.
*   **flameprof**: Generating flamegraphs to visualize performance bottlenecks.
*   **loguru**: Robust logging for formatting, routing, and exception catching.
