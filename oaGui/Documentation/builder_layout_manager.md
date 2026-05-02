# oaGui/Documentation/builder_layout_manager.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for Builder layout synchronization.

## 🚀 Overview
The `BuilderLayoutManager` manages resizing and layout synchronization for individual `LoaderOrchestrator` instances. It ensures that the inner scrollable content correctly adapts to the physical size of the canvas.

## 🏗️ Partitioned Architecture
- **Layer**: Managers (UI Partition)
- **Role**: Layout Sync Manager 📏

## 🔧 Core Functions
### `on_canvas_configure()`
- **Purpose**: Reacts to physical window resizing events.
- **Mechanism**: Uses the `throttle_resize_event` atomic service to debounce updates. ⚡

### `perform_canvas_resize()`
- **Purpose**: Synchronizes the physical canvas dimensions with the inner build frame. 🔄
- **Utility**: Delegates to `synchronize_viewport_dimensions` atomic service.
