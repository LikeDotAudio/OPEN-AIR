# 🏷️ Gui Batch Builder

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
core/gui_batch_builder.py

Handles recursive JSON parsing and Grid layout with a "Skeleton-First" rendering
system.
Pass 1: Structural Elements (OcaBlock, containers) are built immediately.
Pass 2: Functional Elements (Knobs, Faders, etc.) are deferred to keep UI
responsive.
Grid coordinates are shared and pre-calculated to prevent overlaps.

Author: Anthony Peter Kuzub
Version 20260222.Adapter.1

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class GuiBatchBuilderMixin`
Legacy Mixin for Batch Building.
Now acts as a thin wrapper around the standalone AsyncGridRenderer.

##### `_initialize_batch_builder(self)`
Initialize mixin state.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_get_relative_coords(self, widget, ref_widget)`
Calculates coordinates of widget relative to ref_widget.
OPTIMIZED: Caches results to prevent millions of redundant lookups.

**Parameters:**
- `widget`: [TODO: Detail meaning, valid ranges, special cases]
- `ref_widget`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_clear_coord_cache(self)`
Clears the coordinate cache (call on resize).

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_create_dynamic_widgets(self, parent_frame, data, path_prefix, override_cols, on_complete, parent_bg_pil, context)`
Public entry point for creating dynamic widgets using a single-pass synchronized
system.
Delegates to AsyncGridRenderer.

**Parameters:**
- `parent_frame`: [TODO: Detail meaning, valid ranges, special cases]
- `data`: [TODO: Detail meaning, valid ranges, special cases]
- `path_prefix`: [TODO: Detail meaning, valid ranges, special cases]
- `override_cols`: [TODO: Detail meaning, valid ranges, special cases]
- `on_complete`: [TODO: Detail meaning, valid ranges, special cases]
- `parent_bg_pil`: [TODO: Detail meaning, valid ranges, special cases]
- `context`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_process_fields_in_batches(self, *args, **kwargs)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `*args`: [TODO: Detail meaning, valid ranges, special cases]
- `**kwargs`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
