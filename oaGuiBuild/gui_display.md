# 🏷️ Gui Display

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
managers/Display/builder/gui_display.py

This file defines the main Application class, which orchestrates the GUI build
process.

Author: Anthony Peter Kuzub
Blog: www.Like.audio (Contributor to this project)

Professional services for customizing and tailoring this software to your
specific
application can be negotiated. There is no charge to use, modify, or fork this
software.

Build Log: https://like.audio/category/software/spectrum-scanner/
Source Code: https://github.com/APKaudio/
Feature Requests can be emailed to i @ like . audio

Version 20250821.200641.1
--- Standard Debug Logging Setup ---

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class Application`
The main application class that orchestrates the GUI build process.
OPTIMIZED: Implements Persistent Layout Caching and Guarded Logging.

##### `__init__(self, parent, root, mqtt_connection_manager, subscriber_router, state_mirror_engine, state_cache_manager, osc_manager, aes70_manager, snmp_manager, midi_manager, visa_proxy, on_complete)`
Initializes the main Application.

Args:
    parent (tk.Widget): The parent widget.
    root (tk.Tk, optional): The root Tkinter window. Defaults to None.
    mqtt_connection_manager (MqttConnectionManager, optional): The MQTT
connection manager. Defaults to None.
    subscriber_router (MqttSubscriberRouter, optional): The MQTT subscriber
router. Defaults to None.
    state_mirror_engine (StateMirrorEngine, optional): The state mirror engine.
Defaults to None.
    state_cache_manager (StateCacheManager, optional): The state cache manager.
Defaults to None.
    visa_proxy (VisaProxy, optional): The VISA proxy object. Defaults to None.
    on_complete (callable, optional): Callback triggered when initial build pass
is done.

Returns:
    None

**Parameters:**
- `parent`: [TODO: Detail meaning, valid ranges, special cases]
- `root`: [TODO: Detail meaning, valid ranges, special cases]
- `mqtt_connection_manager`: [TODO: Detail meaning, valid ranges, special cases]
- `subscriber_router`: [TODO: Detail meaning, valid ranges, special cases]
- `state_mirror_engine`: [TODO: Detail meaning, valid ranges, special cases]
- `state_cache_manager`: [TODO: Detail meaning, valid ranges, special cases]
- `osc_manager`: [TODO: Detail meaning, valid ranges, special cases]
- `aes70_manager`: [TODO: Detail meaning, valid ranges, special cases]
- `snmp_manager`: [TODO: Detail meaning, valid ranges, special cases]
- `midi_manager`: [TODO: Detail meaning, valid ranges, special cases]
- `visa_proxy`: [TODO: Detail meaning, valid ranges, special cases]
- `on_complete`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_initial_build_complete(self)`
Callback for when the first pass of the GUI build finishes.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_start_background_tab_population(self)`
Starts the background population of unvisited tabs to prevent lag later.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_load_layout_cache(self)`
Loads the layout cache from disk.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_save_layout_cache(self)`
Saves the layout cache to disk.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_make_cache_serializable(self, data)`
Recursively converts Path objects to strings for JSON serialization.

**Parameters:**
- `data`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_restore_cache_paths(self, data)`
Recursively restores Path objects from strings.

**Parameters:**
- `data`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_get_layout_info(self, path)`
Retrieves layout information for a given path, using a cache to avoid redundant
parsing.
Invalidates cache if the directory mtime has changed.

**Parameters:**
- `path`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_add_instance_to_parent(self, parent, instance, index)`
Safely adds a widget instance to a parent using the parent's current geometry
manager.

**Parameters:**
- `parent`: [TODO: Detail meaning, valid ranges, special cases]
- `instance`: [TODO: Detail meaning, valid ranges, special cases]
- `index`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_build_from_directory(self, path, parent_widget, on_complete)`
Recursively builds the GUI from a directory structure.

**Parameters:**
- `path`: [TODO: Detail meaning, valid ranges, special cases]
- `parent_widget`: [TODO: Detail meaning, valid ranges, special cases]
- `on_complete`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `print_to_console(self, message)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `message`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_notebook_right_click(self, event)`
Handles right-click on notebook tabs to open definition.

**Parameters:**
- `event`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_trigger_wysiwyg_editor(self, widget)`
Traverses widget hierarchy to find and invoke definition viewer.

**Parameters:**
- `widget`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_trigger_initial_tab_selection(self)`
Triggers _on_tab_change for initially selected tabs.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_tab_change(self, event)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `event`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_handle_tab_visibility(self, event)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `event`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_global_configure(self, event)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `event`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_resize_finished(self)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `shutdown(self)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `show_splinker_tab(self, src_topic, dest_topic)`
Navigates to the Splinker tab and optionally populates it with topics.

**Parameters:**
- `src_topic`: [TODO: Detail meaning, valid ranges, special cases]
- `dest_topic`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_apply_styles(self, theme_name)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `theme_name`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
