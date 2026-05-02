# oaGui/Documentation/builder_footer.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for the GUI builder telemetry footer.

## 🚀 Overview
The `BuilderFooter` is a specialized telemetry display for the `LoaderOrchestrator`. It provides real-time visual feedback on viewport dimensions, content scale, and MQTT transmission status.

## 🏗️ Partitioned Architecture
- **Layer**: Interface (UI Partition)
- **Role**: Telemetry Display 📊

## 🔧 Core Functions
### `update_dimensions()`
- **Purpose**: Updates the Viewport and Content dimension labels. 📏
- **Visuals**: Features a "pulse" effect (color shift) when dimensions change to draw attention to layout shifts. ⚡

### `log_telemetry_tx()` / `log_command_tx()`
- **Purpose**: Displays a brief log of outgoing MQTT telemetry or command packets. 📤
- **Visuals**: Flashes specific colors (Cyan for Geo, Green for Commands) to indicate network activity. 📡
