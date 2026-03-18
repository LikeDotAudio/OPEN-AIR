# 🏷️ Delete Open Air

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
workers/mqtt/delete_open_air.py

Provides functionality to recursively delete (clear) the entire 'OPEN-AIR' topic
tree
by sending retained empty messages.

Author: Anthony Peter Kuzub
Blog: www.Like.audio (Contributor to this project)

Professional services for customizing and tailoring this software to your
specific
application can be negotiated. There is no charge to use, modify, or fork this
software.

Build Log: https://like.audio/category/software/spectrum-scanner/
Source Code: https://github.com/APKaudio/
Feature Requests can be emailed to i @ like . audio

Version 20260124.000000.1

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Global Functions
#### `delete_open_air_tree(mqtt_connection_manager, state_cache_manager)`
Deletes the OPEN-AIR topic tree.
If state_cache_manager is provided, it uses the cached topics (fastest).

**Parameters:**
- `mqtt_connection_manager`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `state_cache_manager`: [TODO: Detail the precise meaning, valid ranges, and special cases]

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

### Classes
#### `class OpenAirTerminator`
No class description provided.

##### `__init__(self, mqtt_client)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `mqtt_client`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `start_deletion_sequence(self)`
Starts the process: Subscribe -> Collect -> Delete.
Runs in a background thread to avoid blocking GUI.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_execution_thread(self)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `delete_topics(self, topic_list)`
Deletes the provided list of topics by publishing empty retained messages.

**Parameters:**
- `topic_list`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
