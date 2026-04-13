# 🏷️ State Comparator

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
State_Cache/state_comparator.py

Compares incoming MQTT payloads with cached state to determine if an update is
necessary, prioritizing timestamp and falling back to value comparison.

Author: Anthony Peter Kuzub

specific
application can be negotiated. There is no charge to use, modify, or fork this
software.


Version 20250821.200641.1

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Global Functions
#### `should_update(incoming_topic, incoming_payload, cached_state)`
Compare timestamps (timestamp). If incoming > cached, return True.
If timestamp is missing (or in cache missing), compare the entire payload for parity.

**Parameters:**
- `incoming_topic`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `incoming_payload`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `cached_state`: [TODO: Detail the precise meaning, valid ranges, and special cases]

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
