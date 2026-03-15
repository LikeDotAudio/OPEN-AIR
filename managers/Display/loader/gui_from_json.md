# 🏷️ Gui From Json

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
managers/Display/gui_from_json.py

The Universal GUI Wrapper.
This module acts as the "Universal Capacitor," capable of loading ANY
JSON configuration in the system and rendering it via the DynamicGuiBuilder.
It eliminates the need for individual python wrappers for every instrument.

Author: Anthony Peter Kuzub
Blog: www.Like.audio (Contributor to this project)

Professional services for customizing and tailoring this software to your
specific
application can be negotiated. There is no charge to use, modify, or fork this
software.

Build Log: https://like.audio/category/software/spectrum-scanner/
Source Code: https://github.com/APKaudio/
Feature Requests can be emailed to i @ like . audio

Version 20260111.1510.1

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class UniversalGuiLoader`
The Universal Wrapper.
It takes a JSON path and builds the interface.

##### `__init__(self, parent, json_path, config, **kwargs)`
Initialize the Universal GUI Loader.

Args:
    parent: The parent widget (usually a Tab or Window).
    json_path (str): THE CRITICAL COMPONENT. The absolute path to the JSON
blueprint.
    config (dict, optional): Shared application configuration (app_instance,
routers, etc.).
    **kwargs: Standard Tkinter arguments.

**Parameters:**
- `parent`: [TODO: Detail meaning, valid ranges, special cases]
- `json_path`: [TODO: Detail meaning, valid ranges, special cases]
- `config`: [TODO: Detail meaning, valid ranges, special cases]
- `**kwargs`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_init_ui(self)`
Skip the loading label and start the build immediately.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_construct_dynamic_gui(self)`
The Main Event: Handing off to the Builder.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_tab_selected(self, event)`
Optional hook for tab selection events.

**Parameters:**
- `event`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
