# 🏷️ Yak Translator

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
Proxy/yak_manager/yak_translator.py

This file defines the `YakTranslator` class, which acts as the intermediary
(translation layer)
between the application's logic/GUI and the low-level VISA Proxy. It loads YAK
(JSON) command
definitions, processes triggers, builds SCPI commands with substitutions, and
publishes them
to the Proxy's MQTT Tx_Inbox.

Author: Anthony Peter Kuzub
Blog: www.Like.audio (Contributor to this project)

Professional services for customizing and tailoring this software to your
specific
application can be negotiated. There is no charge to use, modify, or fork this
software.

Build Log: https://like.audio/category/software/spectrum-scanner/
Source Code: https://github.com/APKaudio/
Feature Requests can be emailed to i @ like . audio

Version 20260221.Partition.1

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class YakTranslator`
The central translation layer for YAK commands.
It loads command definitions, processes triggers, builds SCPI commands,
and publishes them to the VisaProxy.

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

##### `_load_yak_repository(self)`
Loads the YAK command definitions from the JSON file into memory.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_setup_mqtt_subscriptions(self)`
Subscribes to MQTT topics that trigger YAK command translation.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_yak_trigger_message(self, msg)`
Callback for incoming MQTT messages that trigger YAK command translation.
No try/except here. If something is malformed, the Core crashes and Supervisor
restarts it.

**Parameters:**
- `msg`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_get_command_declaration(self, path_parts)`
Navigates the yak_repository to find the command declaration.

**Parameters:**
- `path_parts`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_fill_scpi_placeholders(self, scpi_template, params)`
Fills placeholders in an SCPI command template.

**Parameters:**
- `scpi_template`: [TODO: Detail meaning, valid ranges, special cases]
- `params`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `retrieve_command_context(self, correlation_id)`
Retrieves and removes the command context associated with a correlation ID.

**Parameters:**
- `correlation_id`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
