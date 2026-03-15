# 🏷️ Blueprint Loader

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
managers/Display/core/blueprint_loader.py

A standalone worker that handles File I/O, Caching, and Merging of GUI
Blueprints.
Decoupled from DynamicGuiBuilder inheritance.

Author: Anthony Peter Kuzub
Blog: www.Like.audio
Version 20260222.Loader.1

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class BlueprintLoader`
Handles File I/O, Hash Verification, and Config Merging.

##### `invalidate_cache()`
Clears the cached default configuration to force a reload from disk.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `load_blueprint(json_filepath, tab_name, last_hash)`
Loads a blueprint from disk, checks hash, merges with default, and normalizes.

Returns:
    tuple: (config_data, new_hash, is_changed)

**Parameters:**
- `json_filepath`: [TODO: Detail meaning, valid ranges, special cases]
- `tab_name`: [TODO: Detail meaning, valid ranges, special cases]
- `last_hash`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_recursively_normalize(config, root)`
Pre-flattens every widget configuration in the tree.

**Parameters:**
- `config`: [TODO: Detail meaning, valid ranges, special cases]
- `root`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_load_default_config()`
Loads the default configuration from managers/Display/default_panel.json
(Optimized).

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_recursive_merge(base, overrides)`
Recursively merges overrides into base.

**Parameters:**
- `base`: [TODO: Detail meaning, valid ranges, special cases]
- `overrides`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
