# oaGui/Documentation/cache_blueprint_store.py
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for GUI default configuration caching.

## 🚀 Overview
The `CacheBlueprintStore` provides a process-lifetime memory cache for GUI default configurations (blueprints). This prevents redundant disk I/O when creating multiple widgets that share the same default panel schema.

## 🏗️ Partitioned Architecture
- **Layer**: Managers (UI Partition)
- **Role**: Configuration Cache 🧠

## 🔧 Core Functions
### `get_cached_default()`
- **Purpose**: Retrieves a deep copy of the cached default configuration. 📡📥📥
- **Outputs**: Returns a `dict` or `None`.

### `set_cached_default()`
- **Purpose**: Sets the process-wide default configuration cache. 💾

### `invalidate()`
- **Purpose**: Clears the memory cache. 🧹
