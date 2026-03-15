# 🏷️ Manager Logic Disconnect Instrument

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
`managers/VisaScipi/manager_visa_disconnect_instrument.py`

This file provides a utility function and manager logic for disconnecting from a VISA (Virtual Instrument Software Architecture) resource. It ensures that communication sessions are gracefully terminated and that the system state is updated to reflect the absence of an instrument.

**Primary Responsibilities:**
- Gracefully close PyVISA instrument sessions.
- Reset the global instrument proxy.
- Broadcast disconnection status and clear device metadata in the UI.

Author: Anthony Peter Kuzub

## ⚙️ Assumptions & Constraints
- Assumes the provided instrument object is a valid PyVISA resource.
- Blocking I/O may occur during the closing handshake.

## 📚 API Reference

### Global Functions
#### `disconnect_instrument(inst)`
Closes the connection to a VISA instrument.

**Parameters:**
- `inst`: The `pyvisa.Resource` instance to close. Can be `None`.

**Returns:**
- `True` if the instrument was successfully closed.
- `False` if no instrument was provided or if an error occurred during the closing process.

**Side Effects & Thread-Safety:**
- Performs blocking I/O to terminate the hardware session.
- Does not modify global state; only affects the provided object.

### Classes
#### `class VisaDisconnector`
Manages the disconnection sequence and state cleanup for VISA instruments.

##### `__init__(self, visa_proxy, gui_publisher)`
Initializes the VisaDisconnector with communication proxies.

**Parameters:**
- `visa_proxy`: The central proxy used to manage the active instrument.
- `gui_publisher`: The dispatcher for status updates.

**Returns:**
- None.

**Side Effects & Thread-Safety:**
- Assigns proxy references to internal state.

##### `disconnect_instrument_logic(self, inst)`
Disconnects the application from the target VISA instrument.

**Parameters:**
- `inst`: The active `pyvisa.Resource` instance. Can be `None`.

**Returns:**
- `True` if the disconnection logic completed successfully.
- `False` if the underlying hardware close operation failed.

**Side Effects & Thread-Safety:**
- Resets the global `visa_proxy` instrument instance to `None`.
- Publishes multiple status updates to clear device-specific info.

## 📝 Focus on Intent (Inline Comments)
- If no instrument is present, ensure the proxy is reset and the UI reflects the disconnected state.
- Clear the proxy session regardless of whether the close succeeded, as the session is no longer viable.
- Reset all UI fields to 'N/A' to indicate no active hardware.
