# oaGui/Documentation/interaction_telemetry_service.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for UI telemetry and tracking.

## 🚀 Overview
The `InteractionTelemetryService` tracks widget visibility and geometry across the UI. It provides real-time observability into which UI sections are active and where they are physically positioned on the screen.

## 🏗️ Partitioned Architecture
- **Layer**: Core/Telemetry (Logic)
- **Role**: UI Observability Service 📡📏

## 🔧 Core Functions
### `track_interaction()`
- **Purpose**: Starts tracking a widget (usually a root frame). 👁️
- **Actions**:
    1. Generates unique visibility and geometry MQTT topics. 📡
    2. Binds to `<Map>`, `<Unmap>`, and `<Configure>` events. 🔗

### `_on_geometry_change()`
- **Purpose**: Debounces geometry changes (resizing) to avoid network congestion. ⏲️
- **Mechanism**: Waits for 500ms of "silence" before publishing the final geometry. ⚡

### `_perform_geometry_publish()`
- **Purpose**: Transmits the physical dimensions (W, H) and position (X, Y) of the tracked widget to MQTT. 📤
