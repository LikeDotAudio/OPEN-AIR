# oaGui/Documentation/cache_image_store.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for procedural asset caching.

## 🚀 Overview
The `CacheImageStore` manages disk and memory caching for procedurally generated assets (panels, screws, textures). It is critical for maintaining high performance and low memory overhead in complex UIs.

## 🏗️ Partitioned Architecture
- **Layer**: Core/Factory (Logic)
- **Role**: Procedural Asset Cache 🖼️⚡

## 🔧 Core Functions
### `load_from_cache()`
- **Purpose**: Retrieves a generated image from memory or disk.
- **Optimization**: Prioritizes the **Memory Cache** (`_MEMORY_ASSET_CACHE`) to bypass slow I/O. 🧠
- **Integrity**: Performs a mandatory pixel-data load check to detect and remove corrupted disk cache files. 🛡️

### `save_to_cache()`
- **Purpose**: Saves a newly generated PIL image to both disk and memory caches. 💾

### `get_asset_hash()`
- **Purpose**: Generates a unique SHA256 identifier for an asset based on its type, dimensions, and configuration. 📋
- **Outputs**: Returns a 64-character hex string used as the cache key.
