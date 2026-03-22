# 🏷️ Worker Marker Peak Re Publisher

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
markers/marker_peak_re_publisher.py

This worker listens to the immediate output of the NAB marker command
(Marker_1/value, etc.)
and republishes the received peak value to the final markers repository
location.

Author: Anthony Peter Kuzub

specific
application can be negotiated. There is no charge to use, modify, or fork this
software.


Version 20250821.200641.1

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class MarkerPeakPublisher`
Handles subscriptions to the immediate NAB marker output and republishes the
values
to the correct final Device-ID/Peak topics based on a provided starting device
ID.

##### `__init__(self, mqtt_util, starting_device_id)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `mqtt_util`: [TODO: Detail meaning, valid ranges, special cases]
- `starting_device_id`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_generate_device_map(self, start_id)`
Calculates the next 5 device IDs and maps Marker_1..Marker_6 to them.
Assumes ID format is 'Device-###'.

**Parameters:**
- `start_id`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_setup_subscriptions(self)`
Subscribes to the specific NAB Marker outputs.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_nab_output_and_republish_peak(self, topic, payload)`
Listens to the NAB query results (Marker_X/value), logs the result,
and republishes the peak value to the final Device-ID/Peak topic.

**Parameters:**
- `topic`: [TODO: Detail meaning, valid ranges, special cases]
- `payload`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
