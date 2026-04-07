# 🏷️ Layout Parser

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
oaGui/Assets/layout_parser.py

This module provides the LayoutParser class, which analyzes directory structures
to determine the GUI layout (e.g., PanedWindow, Notebook).

Author: Anthony Peter Kuzub

specific
application can be negotiated. There is no charge to use, modify, or fork this
software.


Version 20250821.200641.1

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class LayoutParser`
Parses directory structures to determine the GUI layout (e.g., PanedWindow,
Notebook).
This is a stateless utility class.

##### `__init__(self, current_version)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `current_version`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_scan_for_gui_files(path)`
Recursively checks if a folder or any of its sub-folders contain a 'gui_*.json'
file.
Uses os.scandir for speed and caches results.

**Parameters:**
- `path`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `parse_directory(self, path)`
Analyzes a directory path to determine its intended GUI layout structure.
Returns a dictionary describing the layout and relevant parsed data.

**Parameters:**
- `path`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
