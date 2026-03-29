# oaComBroker/Documentation/open_air_core.md
#
# Documentation for the safety-critical core services of the broker.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260328.1515.1

# 🏷️ Open Air Core

## 📖 Description & Purpose
### File Level
core/open_air_core.py

The Safety-Critical Core Partition for OPEN-AIR.
Handles MQTT, Hardware Watchdog, and Device Managers.
Statically allocated, strictly typed, headless.

---

## 🏗️ Core Lifecycle Sequence
When `start_core_services()` is invoked via `Entry.py`, the following sequence 
occurs:

1.  **Environment Setup**: Initializes system paths and console encoding.
2.  **Liveness Monitoring**: Starts a hardware watchdog thread to ensure 
    system liveness.
3.  **Manager Orchestration**: Launches the `MqttConnectionManager` and 
    `StateRegistry`.
4.  **Execution Loop**: Enters a high-priority loop that "pets" the watchdog.
5.  **Graceful Teardown**: Cleanly stops all registered managers on exit.

---

## ⚙️ Assumptions & Constraints
- Assumes a POSIX-compliant environment for path handling.
- Requires network access for MQTT communication.
- Expects 'config.ini' to be present and valid.
- Intended to run as a headless, statically allocated service.

---

## 📚 API Reference

### `main()`
Orchestrates the startup, execution, and shutdown of the OPEN-AIR core.

**Parameters:**
- None

**Returns:**
- None. Execution terminates when the main loop is broken.

**Side Effects:**
- Modifies global sys.path.
- Initializes global logging.
- Starts background heartbeat and MQTT threads.
