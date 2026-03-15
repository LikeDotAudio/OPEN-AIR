# GUI Rebuilder

This module (`gui_rebuilder.py`) handles the **Destruction and Reconstruction** of the GUI. It is used when the configuration file changes or a reload is requested.

## Features
- **Clean Slate**: Destroys all child widgets in the scrollable frame.
- **State Clearing**: Resets internal widget trackers.
- **Rebuild Trigger**: Initiates the batch building process.

## Usage
Internal mixin for `DynamicGuiBuilder`.
```python
self._force_rebuild_gui()
```