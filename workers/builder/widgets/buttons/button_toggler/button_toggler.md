# 🏷️ Button Toggler

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
button_toggler/button_toggler.py

This file provides the BuilderButtonTogglerCreator class for creating groups of
radio-style buttons in the GUI.
Updated to support WYSIWYG resizing via the first button in the group.

Author: Anthony Peter Kuzub
Blog: www.Like.audio (Contributor to this project)
Version 20260220.Modular.1

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class BuilderButtonTogglerCreator`
A mixin class that provides the functionality for creating a
group of buttons that behave like radio buttons.

##### `make_button_toggler(self, parent_widget, config_data, context, **kwargs)`
Creates a set of custom buttons that behave like radio buttons.

**Parameters:**
- `parent_widget`: [TODO: Detail meaning, valid ranges, special cases]
- `config_data`: [TODO: Detail meaning, valid ranges, special cases]
- `context`: [TODO: Detail meaning, valid ranges, special cases]
- `**kwargs`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
