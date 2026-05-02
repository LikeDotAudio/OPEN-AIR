# oaGui/Documentation/engine_widget_assembler.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for dynamic widget assembly orchestration.

## 🚀 Overview
The `EngineWidgetAssemblerMixin` orchestrates the creation of dynamic functional widgets from JSON blueprints. It manages coordinate caches and delegates the physical instantiation to atomic factory services.

## 🏗️ Partitioned Architecture
- **Layer**: Managers (UI Partition)
- **Role**: Widget Assembly Orchestrator 🧩

## 🔧 Core Functions
### `_create_dynamic_widgets()`
- **Purpose**: High-level entry point for dynamic widget construction. 🏗️
- **Delegation**: Hands off to the `instantiate_dynamic_widgets` atomic service.

### `_get_relative_coords()`
- **Purpose**: Extract pixel-perfect relative coordinates for widget placement. 📏
- **Utility**: Uses `UICoordinateUtils` with a local coordinate cache.

### `_clear_coord_cache()`
- **Purpose**: Flushes the coordinate cache to ensure a fresh layout pass during rebuilds. 🧹
