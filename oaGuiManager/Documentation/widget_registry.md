# 🏷️ Widget Registry

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
managers/Display/core/widget_registry.py

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class WidgetRegistry`
Centralized registry for widget creators.
Replaces hardcoded GuiWidgetFactoryMixin.

##### `register(cls, *widget_types)`
Decorator to register a widget creator class.

Usage:
    @WidgetRegistry.register("_Fader", "Fader")
    class BuilderFaderCreator:
        ...

**Parameters:**
- `*widget_types`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `get_creator(cls, widget_type)`
Retrieves the creator class for a given widget type.

**Parameters:**
- `widget_type`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `scan_widgets(cls)`
Auto-discovers widgets by walking the workers/builder directory
and importing modules to trigger registration.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
