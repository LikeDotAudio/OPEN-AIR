# 📦 OPEN-AIR Project Dependencies

This document provides a comprehensive breakdown of every package used in the OPEN-AIR project, grouped by their core function within a spectral analysis and instrument control application.

## 🔬 Data Science & Mathematical Computation
*   **numpy**: The foundational library for numerical computing in Python. It provides support for massive, multi-dimensional arrays and matrices, which is essential for processing high-speed spectral data and audio buffers.
*   **pandas**: A powerful data manipulation tool used for analyzing, cleaning, and organizing structured datasets, likely used for handling historical test data or large configuration tables.

## 📊 Visualization & Rendering
*   **matplotlib**: A comprehensive library for creating static, animated, and interactive visualizations. In an analysis app, this is typically used for drawing spectrograms, waveforms, and data plots.
*   **Pillow (PIL)**: The Python Imaging Library. It adds image processing capabilities and is explicitly noted as being required for Matplotlib and Tkinter image support.

## 🎛️ Instrument Control & Hardware Protocols
This suite of packages forms the physical communication bridge to external hardware, oscilloscopes, and spectrum analyzers.

*   **pyvisa**: A Python wrapper for the Virtual Instrument Software Architecture (VISA) API, used for controlling measurement equipment across various buses (GPIB, RS232, USB, Ethernet).
*   **pyusb**: Provides easy USB access to directly interface with hardware that doesn't use standard measurement protocols.
*   **python-usbtmc**: Implements the USB Test & Measurement Class. It allows the application to control USB-connected test equipment directly.
*   **python-vxi11**: A pure Python implementation of the VXI-11 protocol, allowing the software to control LXI (LAN eXtensions for Instrumentation) compatible instruments over standard Ethernet networks.
*   **pyserial**: Facilitates communication through serial ports (like RS-232 or USB-to-Serial adapters), commonly used for communicating with microcontrollers or older lab equipment.

## 🌐 Networking & IoT Messaging
*   **zeroconf**: Implements Multicast DNS (mDNS) service discovery. This allows the application to automatically find compatible instruments and services on the local network without needing hardcoded IP addresses.
*   **scapy**: A highly capable network packet manipulation tool, useful for network scanning, routing mapping, or debugging low-level network instrument connections.
*   **paho-mqtt**: A synchronous MQTT client used for lightweight, publish-subscribe network messaging, often utilized in IoT device communication.
*   **aiomqtt**: The asynchronous version of an MQTT client, allowing the application to handle network messaging without blocking the main event loop or UI.
*   **websocket-client**: Implements the WebSocket protocol, used for real-time bidirectional communication, particularly in NMOS IS-07 event transport.
*   **python-osc**: Implements the Open Sound Control (OSC) protocol. OSC is highly optimized for modern networking technology and is frequently used to share real-time control data between audio software and synthesizers.

## 🎹 Audio & MIDI Integration
*   **mido**: A library for working with MIDI messages and ports, allowing the application to interface with musical instruments, control surfaces, or audio workstations.
*   **python-rtmidi**: A Python binding for RtMidi, providing a fast, cross-platform backend for real-time MIDI input/output. The dependency checker specifically looks for this package and flags a warning if the conflicting, bare `rtmidi` package is installed instead.

## 📄 Document Parsing & Extraction
*   **pdfplumber**: Used for extracting text, tables, and data precisely from PDF files.
*   **beautifulsoup4 (bs4)**: A library for parsing HTML and XML documents. It is excellent for web scraping or extracting structured data from instrument web interfaces.

## 🛠️ System Utilities & Performance
*   **psutil**: A cross-platform library for retrieving information on running processes and system utilization (CPU, memory, disks, network) to monitor application health.
*   **orjson**: An ultra-fast, highly optimized JSON parsing library, vital for quickly serializing/deserializing large configurations or network payloads.
*   **flameprof**: A profiling tool used to generate flamegraphs. It helps developers visualize code performance bottlenecks and optimize execution time.
*   **loguru**: A highly robust logging library that simplifies formatting, routing, and exception catching (used extensively for the project's visual logging strategy).

## 🧱 Standard Built-in Libraries
The dependency checker also explicitly verifies the availability of several standard Python libraries:

*   **csv**: For reading and writing comma-separated value files.
*   **threading**: For running concurrent background tasks.
*   **subprocess**: For spawning new processes, executing terminal commands, and connecting to their input/output/error pipes.
*   **pathlib**: For object-oriented filesystem path manipulation.
*   **json**: The standard library for JSON encoding and decoding.
