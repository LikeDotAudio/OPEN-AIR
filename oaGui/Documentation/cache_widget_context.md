# oaGui/Documentation/cache_widget_context.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for the widget creation context.

## 🚀 Overview
The `WidgetContext` is a strictly typed, immutable context object used during widget creation. It replaces loose keyword arguments, improving transparency, debugging, and type safety across the GUI builder.

## 🏗️ Partitioned Architecture
- **Layer**: Core/Context (Logic)
- **Role**: Construction Context 🧪

## 🔧 Core Fields
- **state_mirror_engine**: The active state synchronization engine. 🪞
- **subscriber_router**: The MQTT event router. 📡
- **builder_instance**: The `LoaderOrchestrator` instance managing the widget. 🏗️
- **transparency_manager**: Reference to the `EngineVisualEffects` service. 🎨

## 🔧 Static Utilities
### `sanitize_geometry()`
- **Purpose**: Enforces a minimum pixel size of 1x1 for all materialized containers. 📐
- **Safety**: Prevents `0x0` dimensions from reaching the X11 backend, avoiding "BadValue" crashes. 🛡️
