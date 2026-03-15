# GUI Style Manager

This module (`gui_style_manager.py`) manages the application-wide **Theming System**. It configures Tkinter's `ttk.Style` database, defining colors, fonts, and widget appearances based on the selected theme (e.g., "Dark", "Light").

## Features
- **Theme Application**: Applies color palettes to standard widgets (Buttons, Frames, Labels).
- **Custom Styles**: Defines specific style classes (e.g. `Custom.TButton`, `Custom.Treeview`).
- **Dynamic Maps**: Handles hover/active states for complex widgets.

## Usage
Internal mixin for `DynamicGuiBuilder`.
```python
self._apply_styles(theme_name="dark")
```