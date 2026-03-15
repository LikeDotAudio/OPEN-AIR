# Visibility Snitch

This module (`hidden_visibility_manager.py`) is a background service (Mixin) that reports whether the GUI tab is currently **Visible** to the user.

## Features
- **Events**: Listens for Map (Show) and Unmap (Hide) events.
- **Reporting**: Publishes `visible: true/false` to MQTT.
- **Topic**: `.../visibility/visible`

## Usage
Internal logic. Automatically active.