# oaGui/Documentation/sync_behavior.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for background synchronization behavior.

## 🚀 Overview
The `SyncBehavior` defines how background textures and colors are synchronized across the UI tree. It acts as an adapter between widgets and the `EngineVisualEffects` engine.

## 🏗️ Partitioned Architecture
- **Layer**: Workers (UI Partition)
- **Role**: Texture Sync Adapter 🔄

## 🔧 Core Functions
### `register_for_bg_sync()`
- **Purpose**: Registers a widget for automatic background synchronization with its parent. 🔗
- **Actions**:
    1. Binds a `perform_sync` routine to the parent's `<Configure>` event. 📏
    2. Ensures the widget's background color matches the parent's.
    3. Triggers the internal background slicing method (`_perform_background_slice`). 🖼️
