# oaGui/Documentation/json_blueprint_reader.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for blueprint ingestion and merging.

## 🚀 Overview
The `JsonBlueprintReader` orchestrates the ingestion of GUI blueprints. It handles File I/O, integrity verification, and merging with system defaults to ensure theme and schema consistency.

## 🏗️ Partitioned Architecture
- **Layer**: FileReaders (UI Partition)
- **Role**: Blueprint Ingestion Engine 📄🏗️

## 🔧 Core Functions
### `load_blueprint()`
- **Purpose**: Prepares a GUI configuration for the builder.
- **Phases**:
    1. **I/O**: Reads the JSON file using `orjson`. 📡📥📥
    2. **Security**: Generates a SHA256 hash for change detection. 🛡️
    3. **Merging**: Merges specific config with global defaults. 🔄
    4. **Normalization**: Recursively flattens the schema via `JsonSchemaNormalizer`. 📏

### `invalidate_cache()`
- **Purpose**: Forces a flush of the blueprint cache, ensuring fresh defaults are loaded from disk. 🧹
