# 🏷️ Preset From Device

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
presets/preset_from_device.py

A worker module to handle the logic for querying, parsing, and presenting
presets stored on the connected instrument via MQTT.

Author: Anthony Peter Kuzub

specific
application can be negotiated. There is no charge to use, modify, or fork this
software.


Version 20250821.200641.1

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class PresetFromDeviceWorker`
A worker class that manages preset operations on the device via MQTT.

##### `__init__(self, mqtt_util)`
Initializes the worker and subscribes to the necessary topic.

**Parameters:**
- `mqtt_util`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_mqtt_message(self, topic, payload)`
A private callback to capture the preset list when it arrives from the device.

**Parameters:**
- `topic`: [TODO: Detail meaning, valid ranges, special cases]
- `payload`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `get_presets_from_device(self)`
Triggers the device to query its presets. This function is non-blocking.
The result is handled by the _on_mqtt_message callback.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `parse_presets_from_device(self, raw_preset_string)`
Parses a raw, comma-separated string of preset data and returns a list
of valid filenames ending in '.STA'.

**Parameters:**
- `raw_preset_string`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `publish_presets_to_repository(self, preset_list)`
Takes a list of preset filenames and publishes the full preset data
dictionary as a single JSON payload to one topic per preset.

**Parameters:**
- `preset_list`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `present_presets_from_device(self, preset_filename)`
Sets the specified preset filename and triggers the device to store it.

**Parameters:**
- `preset_filename`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
