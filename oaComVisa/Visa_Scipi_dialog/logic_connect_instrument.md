# 🏷️ Manager Logic Connect Instrument

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
`managers/VisaScipi/manager_logic_connect_instrument.py`

This file provides the logic for connecting to a VISA instrument. It manages the lifecycle of the connection, including resource allocation through PyVISA and instrument identification via SCPI *IDN? queries.

**Primary Responsibilities:**
- Establish low-level VISA communication links.
- Coordinate instrument-specific initialization (timeouts, terminations).
- Extract and broadcast hardware metadata (manufacturer, model, etc.).

Author: Anthony Peter Kuzub

## ⚙️ Assumptions & Constraints
- Requires a valid VISA backend (e.g., NI-VISA, Keysight, or PyVISA-py).
- Assumes instruments support standard IEEE 488.2 SCPI *IDN? queries.
- Networked instruments must be reachable via the local system's I/O layer.

## 📚 API Reference

### Classes
#### `class VisaConnector`
Manages the connection lifecycle for VISA-compliant instruments.

##### `__init__(self, visa_proxy, gui_publisher)`
Initializes the VisaConnector with communication proxies.

**Parameters:**
- `visa_proxy`: The central proxy object used to store the active instrument session. Must not be None.
- `gui_publisher`: The MQTT or GUI event dispatcher used to broadcast status updates. Must not be None.

**Returns:**
- None.

**Side Effects & Thread-Safety:**
- Assigns proxy references to internal state. Not thread-safe if multiple threads attempt to initialize the same instance.

##### `setup_visa_instrument(self, resource_name)`
Establishes a connection to a VISA instrument.

**Parameters:**
- `resource_name`: A string representing the VISA resource address (e.g., 'TCPIP::192.168.1.1::INSTR', 'GPIB0::7::INSTR').

**Returns:**
- A `pyvisa.Resource` object on success.
- `None` if the connection fails or the resource is unavailable.

**Side Effects & Thread-Safety:**
- Performs blocking I/O to initialize the hardware interface.
- Configures instrument timeout (5s) and termination characters.

##### `connect_instrument_logic(self, resource_name)`
Handles the full connection sequence to a VISA instrument.

**Parameters:**
- `resource_name`: The VISA resource address string.

**Returns:**
- The `pyvisa.Resource` instance on success.
- `False` if the connection or identification query fails.

**Side Effects & Thread-Safety:**
- Updates the global `visa_proxy` with the new instrument session.
- Dispatches multiple MQTT/GUI status messages for device metadata.
- Performs synchronous SCPI queries; may block the calling thread.

## 📝 Focus on Intent (Inline Comments)
- Set default communication parameters required for reliable SCPI message exchange (timeout, terminations).
- Update the central proxy so other managers can access the active instrument session.
- Query instrument identity using standard SCPI `*IDN?` queries.
- Broadcast hardware metadata to the GUI and monitoring layers.
