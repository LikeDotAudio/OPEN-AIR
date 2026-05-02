# oaGui/Documentation/json_schema_harmonizer.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for schema normalization and translation.

## 🚀 Overview
The `SchemaHarmonizer` translates "Universal Rhyme" schema (shorthand) into the flattened, explicit schema expected by concrete widget creators. It handles style inheritance, label mapping, and unit resolution.

## 🏗️ Partitioned Architecture
- **Layer**: FileReaders (UI Partition)
- **Role**: Schema Translation Engine 🗺️

## 🔧 Core Functions
### `_harmonize_widget_config()`
- **Purpose**: Normalizes a single widget configuration block.
- **Actions**:
    1. Resolves shorthand lexicon (e.g. `w` -> `width`). ⚡
    2. Applies style inheritance from the global registry. 🎨
    3. Maps structured "Pillars" (Geometry, Domain, etc.) to flat keys.
    4. Resolves semantic layout (sticky bits). 📏
    5. Aliases widget types based on orientation and intent. 🔄
- **Outputs**: Returns a homogenized dictionary ready for widget instantiation.
