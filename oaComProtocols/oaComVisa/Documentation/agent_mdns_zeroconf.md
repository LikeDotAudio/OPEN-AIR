# 🏷️ Agent Mdns Zeroconf

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
workers/discovery_agents/agent_mdns_zeroconf.py

Dedicated module for mDNS/ZeroConf discovery (critical for AES70 _oca._tcp).
Also includes legacy IP-based port scanning for VISA/SCPI instruments.

Author: Gemini Agent


## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Global Functions
#### `discover_aes70_devices(timeout)`
Scans for AES70 devices using mDNS.

**Parameters:**
- `timeout`: [TODO: Detail the precise meaning, valid ranges, and special cases]

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

#### `_get_local_ip()`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- None

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

#### `_check_host(ip)`
Legacy: Checks for Port 111 (VXI-11) and Port 5025 (SCPI).

**Parameters:**
- `ip`: [TODO: Detail the precise meaning, valid ranges, and special cases]

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

#### `discover_ip_devices()`
Legacy: Hunts the local network for VISA/SCPI devices.
Renamed internally to avoid conflict, but exported for orchestrator.

**Parameters:**
- None

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

### Classes
#### `class AES70DiscoveryListener`
Listens for AES70 (_oca._tcp) devices on the network.

##### `__init__(self)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `update_service(self, zc, type_, name)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `zc`: [TODO: Detail meaning, valid ranges, special cases]
- `type_`: [TODO: Detail meaning, valid ranges, special cases]
- `name`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `remove_service(self, zc, type_, name)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `zc`: [TODO: Detail meaning, valid ranges, special cases]
- `type_`: [TODO: Detail meaning, valid ranges, special cases]
- `name`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `add_service(self, zc, type_, name)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `zc`: [TODO: Detail meaning, valid ranges, special cases]
- `type_`: [TODO: Detail meaning, valid ranges, special cases]
- `name`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
