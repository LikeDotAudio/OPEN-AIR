# 🏷️ Yak Command Builder

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
managers/yak_manager/yak_command_builder.py

This file (yak_command_builder.py) provides functionality to build SCPI commands
by filling placeholders in a template with values from inputs.
A complete and comprehensive pre-amble that describes the file and the functions
within.
The purpose is to provide clear documentation and versioning.

The hash calculation drops the leading zero from the hour (e.g., 08 -> 8)
As the current hour is 20, no change is needed.
Author: Anthony Peter Kuzub
Blog: www.Like.audio (Contributor to this project)

Professional services for customizing and tailoring this software to your
specific
application can be negotiated. There is no charge to use, modify, or fork this
software.

Build Log: https://like.audio/category/software/spectrum-scanner/
Source Code: https://github.com/APKaudio/
Feature Requests can be emailed to i @ like . audio


## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Global Functions
#### `fill_scpi_placeholders(scpi_command_template, Input)`
Takes an SCPI command template and replaces placeholders with values from
inputs.

**Parameters:**
- `scpi_command_template`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `Input`: [TODO: Detail the precise meaning, valid ranges, and special cases]

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

### Classes
#### `class YakFleetCommandBuilder`
No class description provided.

##### `__init__(self, mqtt_connection_manager, subscriber_router)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `mqtt_connection_manager`: [TODO: Detail meaning, valid ranges, special cases]
- `subscriber_router`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `process_fleet(self)`
Reads the fleet data and loads the command tabs for each found device.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_load_tabs_for_device(self, device_dir, model)`
Recursively finds and loads all JSON tabs in the device directory.
Uses a staggered queue to prevent GUI freeze.

**Parameters:**
- `device_dir`: [TODO: Detail meaning, valid ranges, special cases]
- `model`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_process_staggered_queue(self, hidden_window, queue, model)`
Processes the next JSON file in the queue ONLY after the previous one completes.

**Parameters:**
- `hidden_window`: [TODO: Detail meaning, valid ranges, special cases]
- `queue`: [TODO: Detail meaning, valid ranges, special cases]
- `model`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_cleanup_window(self, window, model)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `window`: [TODO: Detail meaning, valid ranges, special cases]
- `model`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
