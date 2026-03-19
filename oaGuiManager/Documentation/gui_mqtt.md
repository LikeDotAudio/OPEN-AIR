# GUI MQTT Manager

This module (`gui_mqtt_manager.py`) handles the **MQTT Context** for the builder. It determines the base topic path based on the file location and provides helper methods for publishing data.

## Features
- **Path Resolution**: Calculates the correct MQTT topic root relative to the project structure.
- **Publishing**: Centralized `_transmit_command` and `_publish_json_to_topic`.

## Usage
Internal mixin for `DynamicGuiBuilder`.