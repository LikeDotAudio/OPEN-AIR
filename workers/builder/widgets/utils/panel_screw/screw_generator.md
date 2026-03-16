# 🏷️ Screw Generator

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
No top-of-file comment provided. [TODO: Clearly state the file's purpose and its
primary responsibilities. (GNU)]

[TODO: Document specific platform requirements, ABI expectations, or required
privileges. (GNU)]

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class ScrewGenerator`
Procedural generator for high-fidelity Robertson screws.
Supports Fillister (Domed) and Countersunk heads with physical lighting and wear
models.

##### `generate_screw(size_px, config)`
Generates a single screw image (RGBA) centered in a square canvas.
Includes disk caching to prevent redundant generation.

**Parameters:**
- `size_px`: [TODO: Detail meaning, valid ranges, special cases]
- `config`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_hex_to_rgb(hex_str)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `hex_str`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
