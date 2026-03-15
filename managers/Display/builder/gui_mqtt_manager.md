# 🏷️ Gui Mqtt Manager

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
core/gui_mqtt_manager.py

Handles MQTT Context and Command Transmission.

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
#### `class GuiMqttManagerMixin`
Handles MQTT Context and Command Transmission.

##### `_initialize_mqtt_context(self, json_filepath, app_constants, base_mqtt_topic_from_path)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `json_filepath`: [TODO: Detail meaning, valid ranges, special cases]
- `app_constants`: [TODO: Detail meaning, valid ranges, special cases]
- `base_mqtt_topic_from_path`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_subscribe_to_rebuild_requests(self)`
Subscribes to the UI Rebuild topic to allow live updates from external editors.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_publish_json_to_topic(self, json_data)`
Publishes the entire JSON data to the base topic.

**Parameters:**
- `json_data`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_publish_initial_widget_states(self, config_data)`
Recursively scans the config_data for widgets and publishes their initial
values.
This ensures all topics exist in the broker/SNMP bridge immediately on load.

**Parameters:**
- `config_data`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_transmit_command(self, widget_name, value)`
Centralized method for sending GUI updates to MQTT.

**Parameters:**
- `widget_name`: [TODO: Detail meaning, valid ranges, special cases]
- `value`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
