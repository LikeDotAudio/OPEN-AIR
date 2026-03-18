# 🏷️ Discovery Orchestrator

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
workers/discovery_agents/discovery_orchestrator.py

Unified discovery orchestrator that dispatches agents and collects findings.
Decoupled: All hardware operations now run in a dedicated background thread.

Author: Gemini Agent


## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class DiscoveryOrchestrator`
Orchestrates protocol-agnostic fleet discovery.
⚡ THREADED: Discovery operations are isolated to prevent main thread stalls.

##### `__init__(self, manager_ref, aes70_manager)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `manager_ref`: [TODO: Detail meaning, valid ranges, special cases]
- `aes70_manager`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_should_skip_connection(self, serial)`
Returns True if the device is in a cooling-off period.

**Parameters:**
- `serial`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `scan_and_manage_fleet(self)`
⚡ NON-BLOCKING: Requests a scan. Returns immediately.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_discovery_worker_loop(self)`
⚡ THE WORKHORSE: Dedicated thread for all discovery blocking calls.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_perform_actual_discovery(self)`
Internal method called only by the background thread.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_save_fleet_inventory(self)`
Serializes the current inventory to fleet_inventory.json.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_setup_new_active_device(self, device_identifier, device_entry)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `device_identifier`: [TODO: Detail meaning, valid ranges, special cases]
- `device_entry`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_emit_inventory_update(self)`
Sends updates to the Manager. Called via after() from worker thread.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `get_proxy_for_device(self, serial)`
Returns the proxy instance for a given serial, or None if not found.

**Parameters:**
- `serial`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `shutdown(self)`
Shuts down all managed proxies and stops the worker thread.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
