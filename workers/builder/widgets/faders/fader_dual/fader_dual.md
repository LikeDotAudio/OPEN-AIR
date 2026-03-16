# 🏷️ Fader Dual

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
fader_dual/dynamic_guimake_fader_dual.py

A high-performance, photorealistic dual fader widget.
Refactored for zero-flicker tagged updates and debounced resizing.

Author: Anthony Peter Kuzub
Blog: www.Like.audio (Contributor to this project)
Version 20260220.Modular.5

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Global Functions
#### `get_3d_dual_fader_cap(w, h, body_color, outline_color, is_vertical)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `w`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `h`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `body_color`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `outline_color`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `is_vertical`: [TODO: Detail the precise meaning, valid ranges, and special cases]

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

### Classes
#### `class CustomDualFaderFrame`
No class description provided.

##### `__init__(self, master, config, path, state_mirror_engine, base_mqtt_topic, subscriber_router, orientation)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `master`: [TODO: Detail meaning, valid ranges, special cases]
- `config`: [TODO: Detail meaning, valid ranges, special cases]
- `path`: [TODO: Detail meaning, valid ranges, special cases]
- `state_mirror_engine`: [TODO: Detail meaning, valid ranges, special cases]
- `base_mqtt_topic`: [TODO: Detail meaning, valid ranges, special cases]
- `subscriber_router`: [TODO: Detail meaning, valid ranges, special cases]
- `orientation`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_configure(self, event)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `event`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_update_positions(self, *args)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `*args`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `render(self)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_get_handle_under_mouse(self, x, y)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `x`: [TODO: Detail meaning, valid ranges, special cases]
- `y`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

#### `class BuilderFaderDualCreator`
No class description provided.

##### `make(parent_widget, config_data, context, **kwargs)`
Static factory method for creating a dual fader widget.

**Parameters:**
- `parent_widget`: [TODO: Detail meaning, valid ranges, special cases]
- `config_data`: [TODO: Detail meaning, valid ranges, special cases]
- `context`: [TODO: Detail meaning, valid ranges, special cases]
- `**kwargs`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `make_fader_dual(self, parent_widget, config_data, context, **kwargs)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

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
