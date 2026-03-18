# 🏷️ Mqtt Message

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
mqtt/mqtt_message.py

Defines the standardized MqttMessage dataclass for the application.
Enforces strict typing for all MQTT traffic between partitions.

Author: Anthony P. Kuzub(Refactored)
Version 20260221.1

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class MqttMessage`
Standardized MQTT message container.
Frozen to ensure immutability as it passes through the system.

##### `decode_payload(self)`
Helper to ensure payload is a string.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `get_json_payload(self)`
Helper to ensure payload is a dictionary or list (parsed JSON).

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `to_dict(self)`
Converts to a dictionary for publishing.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
