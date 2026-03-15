# 🏷️ Knob Rotary Selector

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
workers/builder/knob_rotary_selector/knob_rotary_selector.py

A specialized knob for multi-position rotary switching.
Supports Industrial Transparency and procedural rendering.

Author: Anthony Peter Kuzub
Blog: www.Like.audio (Contributor to this project)
Version 20260223.Modernized.1

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class RotarySelectorSwitch`
A specialized frame for a multi-position selector switch.
Inherits from CustomKnobFrame to leverage common event handling and state.

##### `__init__(self, parent, variable, positions, continuous, path, state_mirror_engine, *args, **kwargs)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `parent`: [TODO: Detail meaning, valid ranges, special cases]
- `variable`: [TODO: Detail meaning, valid ranges, special cases]
- `positions`: [TODO: Detail meaning, valid ranges, special cases]
- `continuous`: [TODO: Detail meaning, valid ranges, special cases]
- `path`: [TODO: Detail meaning, valid ranges, special cases]
- `state_mirror_engine`: [TODO: Detail meaning, valid ranges, special cases]
- `*args`: [TODO: Detail meaning, valid ranges, special cases]
- `**kwargs`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_draw_selector(self, canvas, width, height, current_idx, positions, fg_color, accent_color, indicator_color, secondary, shape, pointer_style, knob_style, no_center, continuous, main_label, selection_text, show_label)`
Internal drawing pipeline for the selector switch.

**Parameters:**
- `canvas`: [TODO: Detail meaning, valid ranges, special cases]
- `width`: [TODO: Detail meaning, valid ranges, special cases]
- `height`: [TODO: Detail meaning, valid ranges, special cases]
- `current_idx`: [TODO: Detail meaning, valid ranges, special cases]
- `positions`: [TODO: Detail meaning, valid ranges, special cases]
- `fg_color`: [TODO: Detail meaning, valid ranges, special cases]
- `accent_color`: [TODO: Detail meaning, valid ranges, special cases]
- `indicator_color`: [TODO: Detail meaning, valid ranges, special cases]
- `secondary`: [TODO: Detail meaning, valid ranges, special cases]
- `shape`: [TODO: Detail meaning, valid ranges, special cases]
- `pointer_style`: [TODO: Detail meaning, valid ranges, special cases]
- `knob_style`: [TODO: Detail meaning, valid ranges, special cases]
- `no_center`: [TODO: Detail meaning, valid ranges, special cases]
- `continuous`: [TODO: Detail meaning, valid ranges, special cases]
- `main_label`: [TODO: Detail meaning, valid ranges, special cases]
- `selection_text`: [TODO: Detail meaning, valid ranges, special cases]
- `show_label`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

#### `class BuilderKnobRotarySelectorCreator`
Factory for creating Rotary Selector Switch widgets.

##### `make(parent_widget, config_data, context, **kwargs)`
Static factory method for the registry.

**Parameters:**
- `parent_widget`: [TODO: Detail meaning, valid ranges, special cases]
- `config_data`: [TODO: Detail meaning, valid ranges, special cases]
- `context`: [TODO: Detail meaning, valid ranges, special cases]
- `**kwargs`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `make_knob_rotary_selector(parent_widget, config_data, context, **kwargs)`
Main entry point for creating a rotary selector.

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
