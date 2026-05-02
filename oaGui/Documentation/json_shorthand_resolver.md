# oaGui/Documentation/json_shorthand_resolver.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for JSON key shorthand resolution.

## 🚀 Overview
The `JsonShorthandResolver` identifies and translates abbreviated keys into full engine-expected terms. This allows for extremely compact JSON blueprints while maintaining internal clarity.

## 🏗️ Partitioned Architecture
- **Layer**: FileReaders (UI Partition)
- **Role**: Shorthand Lexicon Mapper 📋

## 🔧 Core Functions
### `resolve()`
- **Purpose**: Recursively resolves shorthands in a configuration dictionary. ⚡
- **Mappings**:
    - `lbl` -> `label`
    - `w`/`W` -> `width`
    - `h`/`H` -> `height`
    - `sub` -> `path`
    - `bg`/`fg` -> `bg_color`/`text_color`
- **Special Handling**: Translates `x`/`y` into `row`/`column` when in a layout context, or `width`/`height` in a geometry context. 📏
