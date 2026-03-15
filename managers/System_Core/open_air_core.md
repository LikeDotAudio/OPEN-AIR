# 🏷️ Open Air Core

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
core/open_air_core.py

The Safety-Critical Core Partition for OPEN-AIR.
Handles MQTT, Hardware Watchdog, and Device Managers.
Statically allocated, strictly typed, headless.

Author: Anthony P. Kuzub(Refactored)

## ⚙️ Assumptions & Constraints
- Assumes a POSIX-compliant environment for path handling.
- Requires network access for MQTT communication if configured.
- Expects 'config.ini' to be present and valid.
- Intended to run as a headless, statically allocated, and strictly typed service.
- Requires appropriate permissions to write to the log directory and interact with hardware if needed.

## 📚 API Reference

### Global Functions
#### `main()`
Orchestrates the startup, execution, and shutdown of the OPEN-AIR core.

**Parameters:**
- None

**Returns:**
- None. Execution terminates when the main loop is broken or an unhandled exception occurs. Success is indicated by a graceful shutdown sequence.

**Side Effects & Thread-Safety:**
- Modifies global sys.path.
- Initializes global logging and console encoding.
- Starts background heartbeat and MQTT threads.
- Performs I/O operations (filesystem and network).
- This function is not reentrant and should only be called once as the main entry point.

## 📝 Focus on Intent (Inline Comments)
- Prepend project root to sys.path to ensure local imports take precedence.
- Establish a dedicated log partition for the CORE to simplify debugging.
- Heartbeat ensures the system can be recovered by hardware if it hangs.
- Continually pet the watchdog to prevent a system reset.
- Yield CPU to avoid 100% usage while idling.
