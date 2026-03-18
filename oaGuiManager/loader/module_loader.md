# 🏷️ Module Loader

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
oaGuiDefinitions/module_loader.py

Handles dynamic loading of Python modules and instantiation of GUI classes.
Updated to wrap pure Python modules in a DynamicGuiBuilder for background
inheritance.

Author: Anthony Peter Kuzub
Blog: www.Like.audio (Contributor to this project)
Version 20260218.Optimization.2

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class ModuleLoader`
Handles dynamic loading of Python modules and instantiation of GUI classes.

##### `__init__(self, theme_colors, state_mirror_engine, subscriber_router, app_instance)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `theme_colors`: [TODO: Detail meaning, valid ranges, special cases]
- `state_mirror_engine`: [TODO: Detail meaning, valid ranges, special cases]
- `subscriber_router`: [TODO: Detail meaning, valid ranges, special cases]
- `app_instance`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `load_and_instantiate_gui(self, path, parent_widget, class_filter)`
Loads a module from a given path and instantiates the GUI class.
Uses os.scandir for optimized file discovery.

**Parameters:**
- `path`: [TODO: Detail meaning, valid ranges, special cases]
- `parent_widget`: [TODO: Detail meaning, valid ranges, special cases]
- `class_filter`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
