# oaGui/Documentation/loader_lifecycle_service.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for UI destruction and re-initialization.

## 🚀 Overview
The `LifecycleManagerMixin` handles the lifecycle events of the GUI frames, specifically focusing on optimized destruction and re-initialization of content using atomic services.

## 🏗️ Partitioned Architecture
- **Layer**: Managers (UI Partition)
- **Role**: Lifecycle Manager ♻️

## 🔧 Core Functions
### `_force_rebuild_gui()`
- **Purpose**: Forces a complete rebuild of the GUI.
- **Actions**:
    1. Invalidates UI render caches. 🧹
    2. Clears the last build hash.
    3. Triggers a fresh load and build from file. 🏗️

### `_rebuild_gui()`
- **Purpose**: Delegates the reconstruction of the UI to the atomic `orchestrate_ui_rebuild` service. 🔄
