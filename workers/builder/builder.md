# 🏷️ Builder

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
builder/builder.py

This file defines the main DynamicGuiBuilder class, which is responsible for
constructing the application's GUI from a JSON configuration.

Author: Anthony Peter Kuzub
Blog: www.Like.audio (Contributor to this project)

Professional services for customizing and tailoring this software to your
specific
application can be negotiated. There is no charge to use, modify, or fork this
software.

Build Log: https://like.audio/category/software/spectrum-scanner/
Source Code: https://github.com/APKaudio/
Feature Requests can be emailed to i @ like . audio

Version 20260222.Refactored.1

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class AutoScrollbar`
A scrollbar that hides itself when it's not needed.

##### `set(self, lo, hi)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `lo`: [TODO: Detail meaning, valid ranges, special cases]
- `hi`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

#### `class DynamicGuiBuilder`
No class description provided.

##### `__init__(self, parent, json_path, tab_name, *args, **kwargs)`
Initializes the DynamicGuiBuilder.

**Parameters:**
- `parent`: [TODO: Detail meaning, valid ranges, special cases]
- `json_path`: [TODO: Detail meaning, valid ranges, special cases]
- `tab_name`: [TODO: Detail meaning, valid ranges, special cases]
- `*args`: [TODO: Detail meaning, valid ranges, special cases]
- `**kwargs`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_right_click(self, event)`
Displays context menu on right click.

**Parameters:**
- `event`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_show_wysiwyg_editor(self)`
Opens the WYSIWYG Editor in a separate process, ensuring only ONE instance
exists system-wide.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_check_dependencies(self)`
Manually triggers the Installation/Setup script to verify dependencies.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_clear_panel_background(self)`
Removes the generated panel background and restores the theme default.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_frame_configure(self, event)`
Event handler for when the scrollable frame is configured. It updates the scroll
region of the canvas.

**Parameters:**
- `event`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_canvas_configure(self, event)`
Event handler for when the canvas is configured. It adjusts the width of the
window item within the canvas to match the canvas's width.

**Parameters:**
- `event`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_perform_canvas_resize(self, width)`
Performs the actual resizing of the canvas window item.

**Parameters:**
- `width`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_apply_panel_background(self, panel_config, width, height)`
Generates and applies a procedural patina panel to the whole tab.
Moves heavy PIL generation to a background thread.

**Parameters:**
- `panel_config`: [TODO: Detail meaning, valid ranges, special cases]
- `width`: [TODO: Detail meaning, valid ranges, special cases]
- `height`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_apply_generated_background(self, panel_bg_pil, width, height, task_id)`
Applies the background PIL image to the UI (Main Thread).

**Parameters:**
- `panel_bg_pil`: [TODO: Detail meaning, valid ranges, special cases]
- `width`: [TODO: Detail meaning, valid ranges, special cases]
- `height`: [TODO: Detail meaning, valid ranges, special cases]
- `task_id`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `register_for_slicing(self, callback)`
Adds a callback to be executed when the background is updated.

**Parameters:**
- `callback`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_visibility(self, event)`
Triggered when the tab becomes visible. Handles late-ignition background sync.

**Parameters:**
- `event`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_get_widget_context(self)`
Creates a strictly typed context object for widget creation.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_trigger_background_sync(self, force)`
Calculates settled dimensions and triggers background regeneration with
debouncing.

**Parameters:**
- `force`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_perform_background_sync(self, force)`
Internal execution logic for background sync.

**Parameters:**
- `force`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_trigger_reslice_all(self)`
⚡ BATCH RESLICE ENGINE

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_clear_coord_cache(self)`
Internal optimization: clears cached screen coordinates.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_perform_batch_reslice(self)`
Executes the actual reslice for all widgets using cached shared context.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
