# oaGui/Documentation/json_schema_normalizer.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for recursive schema normalization.

## 🚀 Overview
The `JsonSchemaNormalizer` recursively applies schema normalization to a configuration tree. It ensures that every widget in a nested blueprint is flattened and homogenized before the builder attempts to render it.

## 🏗️ Partitioned Architecture
- **Layer**: Methods (UI Partition)
- **Role**: Recursive Normalizer 🔄

## 🔧 Core Functions
### `normalize()`
- **Purpose**: Recursively normalizes a configuration branch. ⚡
- **Actions**:
    1. Normalizes the current level via the `WidgetSchemaNormalizer`. 📏
    2. Recursively descends into `fields`, `blocks`, or `items` collections.
    3. Skips known metadata keys to optimize processing. 🏎️
- **Outputs**: Returns the fully normalized configuration tree.
