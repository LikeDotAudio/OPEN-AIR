# 🏷️ Element Properties

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
Interface/Tabs/ElementProperties/element_properties.py

The Element Properties Workspace.
Provides a high-level UI for adjusting parameters of the focused element.
Recursively displays all JSON properties on a single page with collapsible
sections.

Author: Gemini CLI

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

#### `class ElementProperties`
A dedicated workspace for editing the properties of a selected element.

##### `__init__(self, parent, *args, **kwargs)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `parent`: [TODO: Detail meaning, valid ranges, special cases]
- `*args`: [TODO: Detail meaning, valid ranges, special cases]
- `**kwargs`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_destroy(self, event)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `event`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_state_updated(self, json_data, source)`
Keep properties in sync if JSON changed elsewhere, but don't force a full redraw
if we are the source.

**Parameters:**
- `json_data`: [TODO: Detail meaning, valid ranges, special cases]
- `source`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_request_debounced_refresh(self, delay)`
Schedules a full properties rebuild after a delay to prevent flickering during
rapid editing.

**Parameters:**
- `delay`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_focus_requested(self, path, source)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `path`: [TODO: Detail meaning, valid ranges, special cases]
- `source`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_refresh_content(self)`
Redraws the entire property tree for the focused element.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_deep_merge_for_display(self, template, actual)`
Creates a merged dictionary containing all template keys and all actual keys.

**Parameters:**
- `template`: [TODO: Detail meaning, valid ranges, special cases]
- `actual`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_build_ui(self)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_delete_focused_element(self)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_render_header_actions(self)`
Renders element-level actions at the top of the properties list.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_render_alignment_quick_tools(self, data, container)`
Specialized UI for L R C T B alignment mapping to 'layout.align'.

**Parameters:**
- `data`: [TODO: Detail meaning, valid ranges, special cases]
- `container`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_render_sticky_quick_tools(self, data, container)`
Specialized UI for NSEW sticky (Stretching).

**Parameters:**
- `data`: [TODO: Detail meaning, valid ranges, special cases]
- `container`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_update_tool_highlights(self, align_str, stretch_str, align_btns, sticky_buttons)`
Helper to sync button colors without a full re-render.

**Parameters:**
- `align_str`: [TODO: Detail meaning, valid ranges, special cases]
- `stretch_str`: [TODO: Detail meaning, valid ranges, special cases]
- `align_btns`: [TODO: Detail meaning, valid ranges, special cases]
- `sticky_buttons`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_render_missing_library_properties(self, data)`
No longer used directly as main pass now proactive, but keeping for standalone
adds.

**Parameters:**
- `data`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_render_recursive_properties(self, data, parent, prefix, depth, actual_data)`
Recursively renders all properties with collapsible headers and structural
controls.

**Parameters:**
- `data`: [TODO: Detail meaning, valid ranges, special cases]
- `parent`: [TODO: Detail meaning, valid ranges, special cases]
- `prefix`: [TODO: Detail meaning, valid ranges, special cases]
- `depth`: [TODO: Detail meaning, valid ranges, special cases]
- `actual_data`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_move_out(self, path)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `path`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_move_in(self, path)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `path`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_render_leaf_editor(self, key, value, parent, full_path, is_virtual)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `key`: [TODO: Detail meaning, valid ranges, special cases]
- `value`: [TODO: Detail meaning, valid ranges, special cases]
- `parent`: [TODO: Detail meaning, valid ranges, special cases]
- `full_path`: [TODO: Detail meaning, valid ranges, special cases]
- `is_virtual`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
