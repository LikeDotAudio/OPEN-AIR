# GUI Batch Builder

This module (`gui_batch_builder.py`) implements the **Asynchronous Construction** logic. Instead of freezing the UI while building 100+ widgets, it builds them in small batches (e.g., 5 at a time) and yields control to the Tkinter main loop.

## Features
- **Non-Blocking**: Keeps the UI responsive during load.
- **Recursive Parsing**: Handles nested structures like `OcaBlock`.
- **Grid Layout**: Manages the grid placement (row/col calculation) for widgets.

## Usage
Internal mixin for `DynamicGuiBuilder`.