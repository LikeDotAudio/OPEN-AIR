# oaGui/Documentation/interaction_dispatcher.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for UI-to-MQTT event dispatching.

## 🚀 Overview
The `InteractionDispatcher` is responsible for transmitting user-driven UI events (button clicks, fader movements) to the network via MQTT. It ensures that every interaction is logged and broadcasted to the wider OPEN-AIR system.

## 🏗️ Partitioned Architecture
- **Layer**: Hooks (UI Partition)
- **Role**: Event Dispatcher 📡📤📤

## 🔧 Core Functions
### `transmit()`
- **Purpose**: Centralized method for sending GUI updates to MQTT.
- **Actions**:
    1. Logs the command locally to the builder's footer. 📋
    2. Calculates the target MQTT topic based on the widget name and path. 📏
    3. Publishes a JSON payload containing the new value, source, and a unique GUID. 📦
- **Integration**: Uses the `StateMirrorEngine` for topic calculation and publication.

### `publish_init_state()`
- **Purpose**: Announces the GUI's entire initial configuration (blueprint) to the network. 🚀
- **Actions**: Publishes to the base module topic with a "GUI-INIT" source tag.
