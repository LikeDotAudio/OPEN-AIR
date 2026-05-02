# oaGui/Documentation/cache_layout_store.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for layout persistence management.

## 🚀 Overview
The `CacheLayoutStore` manages the serialization and restoration of the UI layout cache. It ensures that complex directory-based structures and window geometries are persisted across sessions.

## 🏗️ Partitioned Architecture
- **Layer**: Managers (UI Partition)
- **Role**: Layout Persistence Store 💾

## 🔧 Core Functions
### `load()`
- **Purpose**: Loads the layout cache from disk using high-speed `orjson`. 📡📥📥
- **Outputs**: Returns a dictionary with restored `pathlib.Path` objects.

### `save()`
- **Purpose**: Serializes the current layout state to disk. 📡📤📤
- **Actions**: Converts `Path` objects to strings for JSON compatibility.

## 📡 Interactions
- **Inputs**: Reads from `LAYOUT_CACHE_PATH`.
- **Outputs**: Writes structured JSON to disk. 📁
