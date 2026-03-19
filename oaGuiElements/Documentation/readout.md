# 🏷️ Readout

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
workers/builder/fader/core/readout.py

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class ReadoutDrawer`
No class description provided.

##### `draw_floating_value(canvas, frame, cx, handle_y, value, color)`
Draws the floating value display near the fader cap.

**Parameters:**
- `canvas`: [TODO: Detail meaning, valid ranges, special cases]
- `frame`: [TODO: Detail meaning, valid ranges, special cases]
- `cx`: [TODO: Detail meaning, valid ranges, special cases]
- `handle_y`: [TODO: Detail meaning, valid ranges, special cases]
- `value`: [TODO: Detail meaning, valid ranges, special cases]
- `color`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `update_static_label(frame, value_label, value, active_color)`
Updates the fixed value label below the fader.

**Parameters:**
- `frame`: [TODO: Detail meaning, valid ranges, special cases]
- `value_label`: [TODO: Detail meaning, valid ranges, special cases]
- `value`: [TODO: Detail meaning, valid ranges, special cases]
- `active_color`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
