# Geometry Snitch

This module (`hidden_geometry_manager.py`) is a background service (Mixin) that monitors the **Window Geometry**.

## Features
- **Reporting**: Publishes the window's Position (X, Y) and Size (Width, Height) to MQTT whenever it changes.
- **Topic**: `.../visibility/geometry`

## Usage
Internal logic. Automatically active.
