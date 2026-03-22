# 🏷️ Status Light

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
status_light/header_status_light.py

Adds a status indicator circle to the GUI.
Now a standalone widget compatible with grid-based layout.

Author: Anthony Peter Kuzub

Version 20250821.200641.4

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class StatusLightWidget`
A standalone status light widget that manages its own UI and MQTT subscription.

##### `__init__(self, parent, config, state_mirror_engine, subscriber_router, base_topic_path)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `parent`: [TODO: Detail meaning, valid ranges, special cases]
- `config`: [TODO: Detail meaning, valid ranges, special cases]
- `state_mirror_engine`: [TODO: Detail meaning, valid ranges, special cases]
- `subscriber_router`: [TODO: Detail meaning, valid ranges, special cases]
- `base_topic_path`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_update_status_light(self, msg)`
Callback function to update the status light's color based on MQTT messages.

**Parameters:**
- `msg`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_draw(self)`
Transparency hook.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

#### `class HeaderStatusLightMixin`
Adds a status indicator circle to the GUI.

##### `_build_header_status_light(self, parent_widget, config_data, context)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `parent_widget`: [TODO: Detail meaning, valid ranges, special cases]
- `config_data`: [TODO: Detail meaning, valid ranges, special cases]
- `context`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
