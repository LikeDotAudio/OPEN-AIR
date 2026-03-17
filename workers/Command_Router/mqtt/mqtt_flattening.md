# 🏷️ Mqtt Flattening

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
mqtt/mqtt_flattening.py

A utility module to process and flatten nested MQTT payloads into a format
suitable for display in a flat table or export to CSV. It buffers incoming
messages until a complete set is received, then pivots the data.

Author: Anthony Peter Kuzub
Blog: www.Like.audio (Contributor to this project)

Professional services for customizing and tailoring this software to your
specific
application can be negotiated. There is no charge to use, modify, or fork this
software.

Build Log: https://like.audio/category/software/spectrum-scanner/
Source Code: https://github.com/APKaudio/
Feature Requests can be emailed to i @ like . audio

Version 20250821.200641.1

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class MqttDataFlattenerUtility`
Manages the buffering and flattening of incoming MQTT messages based on dynamic
topic identifiers.

##### `__init__(self, print_to_gui_func)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `print_to_gui_func`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `clear_buffer(self)`
Clears the internal data buffer.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `process_mqtt_message_and_pivot(self, topic, payload, topic_prefix)`
Processes a single MQTT message. It triggers flattening when it detects the
start of a new data set based on the unique identifier.

Args:
    topic (str): The MQTT topic of the message.
    payload (str): The JSON payload of the message.
    topic_prefix (str): The root topic to be used for filtering.

Returns:
    list: A list of dictionaries representing the flattened, pivoted data,
          or an empty list if not all messages have been received.

**Parameters:**
- `topic`: [TODO: Detail meaning, valid ranges, special cases]
- `payload`: [TODO: Detail meaning, valid ranges, special cases]
- `topic_prefix`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_flush_buffer(self, new_topic, new_data, new_identifier)`
Processes and flattens the current buffer.

**Parameters:**
- `new_topic`: [TODO: Detail meaning, valid ranges, special cases]
- `new_data`: [TODO: Detail meaning, valid ranges, special cases]
- `new_identifier`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
