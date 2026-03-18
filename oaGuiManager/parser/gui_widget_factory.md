# GUI Widget Factory

This module (`gui_widget_factory.py`) is the **Registry** that maps JSON widget type strings (e.g., `"_Knob"`, `"_SmartMeter"`) to the specific creator methods in the builder class.

## Features
- **Central Registry**: A single dictionary mapping keys to functions.
- **Aliases**: Handles multiple names for the same widget (e.g. `_SmartGraph` -> `_DataGraph`).
- **Adapter Calls**: Routes complex widgets (like Plots) to their adapter mixins.

## Usage
Internal mixin for `DynamicGuiBuilder`.