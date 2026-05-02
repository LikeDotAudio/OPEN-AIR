# oaGui/Documentation/loader_orchestrator.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for the Dynamic GUI Orchestrator.

## 🚀 Overview
The `LoaderOrchestrator` is the **Main Orchestrator** for the Dynamic GUI Builder. It constructs a pixel-perfect, background-aware industrial UI from a JSON blueprint. It manages scrolling, transparency synchronization, and widget lifecycles.

## 🏗️ Partitioned Architecture
- **Layer**: Workers (UI Partition)
- **Role**: UI Builder Orchestrator 🏗️🎨

## 🔧 Core Functions
### `__init__()`
- **Purpose**: Initializes the state and services for a new UI panel.
- **Actions**:
    1. Resolves parent orchestrator context. 🔗
    2. Initializes state and services (MQTT, State Cache). 📡
    3. Builds the **Scaffolding** (Canvas, Scrollbars, Footer). 🛠️

### `start()`
- **Purpose**: Triggers the physical UI build sequence. 🚀
- **Logic**: Branches between loading from a JSON file or rebuilding from the current internal state.

### `_perform_scroll_sync()`
- **Purpose**: Synchronizes background texture slices during scrolling. 🔄
- **Mechanism**: Debounced via a timer to ensure smooth performance.

### `_get_widget_context()`
- **Purpose**: Factory for the `WidgetContext` object passed to all child widget creators. 🧪

## 📡 Interactions
- **Inbound**: JSON blueprints and MQTT state updates. 📡📥📥
- **Outbound**: Telemetry transmissions and procedural background updates. 📡📤📤
