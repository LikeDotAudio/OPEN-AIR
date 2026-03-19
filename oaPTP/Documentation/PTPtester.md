# 🏷️ Ptptester

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
`managers/PTP/PTPtester.py`

A diagnostic utility for sniffing and reporting PTP (Precision Time Protocol) traffic to the OPEN-AIR system via MQTT.

**Primary Responsibilities:**
- Sniffs PTP event and general messages (UDP 319/320).
- Parses PTP packet headers using Scapy.
- Publishes captured data to a local or remote MQTT broker for application testing.
- Provides a standalone CLI interface for real-time traffic monitoring.

## ⚙️ Assumptions & Constraints
- **Library Dependencies:** Requires `scapy` for packet manipulation and `paho-mqtt` for network communication.
- **Execution Privileges:** Must be executed with root/administrative privileges (e.g., via `sudo`) to access raw network sockets for sniffing.
- **Network Environment:** Assumes a functional MQTT broker is reachable at the specified address if reporting functionality is required.
- **Platform Support:** Primarily designed for Linux-based systems.

## 📚 API Reference

### Global Functions
#### `packet_callback(pkt)`
Analyzes captured network packets and publishes extracted PTP data to the MQTT broker.

**Parameters:**
- `pkt`: A `scapy` packet object representing the captured network frame.

**Returns:**
- `None`.

**Side Effects & Thread-Safety:**
- Prints packet summaries and PTP header details to the standard output.
- Performs network I/O by publishing JSON-encoded data to the configured MQTT topic.
- Not thread-safe if multiple sniffer instances are using a shared global MQTT client.

## 📝 Focus on Intent (Inline Comments)
- **MQTT Compatibility:** We include a try-except block when initializing the `mqtt.Client` to maintain compatibility between older `paho-mqtt` versions and the newer v2.0+ API.
- **Minimal PTP Layer:** If the `scapy-contrib` PTP layer is missing, we define a minimal `PTP` class. This ensures the script remains functional on systems with a basic `scapy` installation.
- **Performance Optimization:** We use `store=0` in the `sniff()` function to prevent the script from accumulating captured packets in memory, which is critical for long-running diagnostic sessions.
- **Fallback Logic:** If a packet on UDP 319/320 isn't automatically identified as PTP, we provide a raw hex dump for diagnostic purposes, helping identify non-standard or malformed PTP implementations.
