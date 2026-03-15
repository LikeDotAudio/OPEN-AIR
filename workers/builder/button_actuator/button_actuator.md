# 🏷️ Button Actuator

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
button_actuator/button_actuator.py

This file provides the BuilderButtonActuatorCreator class for creating
photorealistic
actuator buttons in the GUI using the shared CanvasButton base.

Author: Anthony Peter Kuzub
Blog: www.Like.audio (Contributor to this project)
Version 20260208.2345

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class BuilderButtonActuatorCreator`
A mixin class that provides the functionality for creating photorealistic
actuator buttons that trigger actions via MQTT.

##### `make_button_actuator(self, parent_widget, config_data, context, **kwargs)`
Creates a photorealistic CanvasButton that acts as a momentary actuator.

**Parameters:**
- `parent_widget`: [TODO: Detail meaning, valid ranges, special cases]
- `config_data`: [TODO: Detail meaning, valid ranges, special cases]
- `context`: [TODO: Detail meaning, valid ranges, special cases]
- `**kwargs`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_actuator_state_update(self, msg)`
Syncs the button's visual state with remote MQTT triggers.

**Parameters:**
- `msg`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
