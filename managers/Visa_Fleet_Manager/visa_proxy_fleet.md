# 🏷️ Visa Proxy Fleet

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
managers/STATE_VISA_FLEET_Manager/visa_proxy_fleet.py

Refactored VisaProxy for fleet management, handling device-specific
communication via Manager callbacks.

Author: Gemini Agent


## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Global Functions
#### `_write_safe_fleet(proxy_instance, command)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `proxy_instance`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `command`: [TODO: Detail the precise meaning, valid ranges, and special cases]

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

#### `_query_safe_fleet(proxy_instance, command, correlation_id)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `proxy_instance`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `command`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `correlation_id`: [TODO: Detail the precise meaning, valid ranges, and special cases]

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

### Classes
#### `class VisaProxyFleet`
Manages a single PyVISA connection for a specific instrument in a fleet.
Communicates via callbacks to the managing entity (VisaFleetManager).

##### `__init__(self, manager_ref, device_serial, resource_name, instrument_model, manufacturer)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `manager_ref`: [TODO: Detail meaning, valid ranges, special cases]
- `device_serial`: [TODO: Detail meaning, valid ranges, special cases]
- `resource_name`: [TODO: Detail meaning, valid ranges, special cases]
- `instrument_model`: [TODO: Detail meaning, valid ranges, special cases]
- `manufacturer`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `shutdown(self)`
Shuts down the proxy, stopping the worker thread and clearing resources.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_command_processor_worker(self)`
Worker thread to process commands from the queue.
⚡ OPTIMIZATION: Uses pure blocking get() with a Poison Pill for shutdown (Rule
#5).

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `enqueue_command(self, command, query, correlation_id)`
Public method for the manager to enqueue a command to this proxy.

**Parameters:**
- `command`: [TODO: Detail meaning, valid ranges, special cases]
- `query`: [TODO: Detail meaning, valid ranges, special cases]
- `correlation_id`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `set_instrument_instance(self, inst)`
Sets the PyVISA instrument instance and updates connection status.

**Parameters:**
- `inst`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_reset_device_fleet(self)`
Attempts to reset the connected instrument using standard SCPI commands.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
