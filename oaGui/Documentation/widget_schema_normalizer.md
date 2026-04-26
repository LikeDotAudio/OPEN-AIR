# 🏷️ Widget Schema Normalizer

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
managers/Display/parser/widget_schema_normalizer.py

A standalone normalizer that translates "Universal Rhyme" schema into
the flat schema expected by concrete widget creators.
Decoupled from DynamicGuiBuilder inheritance.

Author: Anthony Peter Kuzub
Version 20260222.Normalized.1

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class WidgetSchemaNormalizer`
Static utility for normalizing widget configurations.

##### `normalize(config, root_config)`
Translates a structured config into a flat one.
Handles _SmartMeter, _SmartKnob, _SmartFader, _SmartGraph aliases.
Supports the new 5-pillar homogenized schema and abbreviation lexicon.

Args:
    config (dict): The raw widget configuration.
    root_config (dict, optional): The root layout config (for style lookups).

**Parameters:**
- `config`: [TODO: Detail meaning, valid ranges, special cases]
- `root_config`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_process_homogenized_schema(config)`
Detects and unpacks the 5-pillar homogenized schema.
Handles the 'items' array for container widgets.

**Parameters:**
- `config`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_expand_abbreviations(data)`
Maps Lexicon Abbreviations to engine-expected keys.
Recursively expands dictionaries to support sub-configurations.

**Parameters:**
- `data`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
