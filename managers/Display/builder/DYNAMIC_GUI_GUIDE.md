# OPEN-AIR Dynamic GUI System: How-To Guide

This guide explains how the OPEN-AIR dynamic GUI system works, how to create new interfaces using JSON blueprints, and how the various components in the `display/` directory interact.

## 🚀 Overview

The OPEN-AIR GUI is built dynamically at runtime from JSON configuration files. This "data-driven" approach allows for rapid prototyping and the ability to create complex, responsive interfaces without writing repetitive Python code for every widget.

### Core Components

1.  **`OpenAir.py`**: The main entry point of the application. It initializes the `Application` class.
2.  **`managers/Display/builder/gui_display.py` (`Application` class)**: The grand orchestrator. It sets up the main window, the sidebars (`left_50`, `right_50`), and triggers the loading of individual GUI modules.
3.  **`managers/Display/loader/gui_from_json.py` (`UniversalGuiLoader`)**: A versatile wrapper that can take any JSON path and render it using the `DynamicGuiBuilder`.
4.  **`workers/builder/builder.py`**: The heart of the system. It parses JSON blueprints and uses various "Creators" (Mixins) to instantiate Tkinter widgets.

---

## 🏗️ How to Add a New GUI

Adding a new interface to OPEN-AIR usually involves creating a JSON file and registering it in the layout.

### 1. Create your JSON Blueprint
Place your JSON file in an appropriate directory (e.g., `display/left_50/top_100/your_module/gui_your_module.json`).

A basic blueprint looks like this:
```json
{
  "MyButton": {
    "type": "_GuiButtonToggle",
    "identity": { "lbl": "Toggle Me" },
    "dynamics": { "sub": "my/mqtt/topic" },
    "geometry": { "x": 0, "y": 0 }
  }
}
```

### 2. Registering in the Layout
The `Application` class in `gui_display.py` uses `ModuleLoader` and `LayoutParser` to automatically find and load GUI components. Generally, placing your files in the standard directory structure is enough for them to be picked up if they follow the `gui_*.py` or `gui_*.json` naming convention and are within the searched paths.

---

## 🛠️ The Recipe: How JSON becomes Widgets

The `DynamicGuiBuilder` follows a strict "recipe" to build your interface:

1.  **Standardization**: The `WidgetSchemaNormalizer` (in `managers/Display/parser/`) ensures every widget definition has a consistent structure, even if some keys are missing in the JSON.
2.  **Registry Lookup**: The `GuiWidgetFactoryMixin` (in `managers/Display/factory/`) looks at the `type` key in your JSON (e.g., `"_GuiButtonToggle"`) and maps it to a specific Creator method.
3.  **Creation**: The Creator method instantiates the widget, applying styles from the `GuiStyleManager`.
4.  **MQTT Binding**: The `GuiMqttManagerMixin` binds the widget to an MQTT topic. When the topic's state changes, the widget updates automatically.
5.  **Placement**: The `AsyncGridRenderer` (in `managers/Display/builder/`) places the widget in the scrollable canvas using a skeleton-first approach.

---

## 🎨 Layout and Styling

### Sidebars and Regions
The screen is divided into regions managed by `gui_display.py`:
-   `left_50`: The left half of the screen.
-   `right_50`: The right half of the screen.
-   Sub-regions like `top_10`, `bottom_90` allow for further nesting.

### Themes
The system supports themes defined in `workers/styling/style.py`. You can specify a theme in your JSON or let it inherit the system default (usually "dark").

---

## 🧪 Testing your GUI
You can use the `UniversalGuiLoader` to test a standalone JSON file.

```python
from managers.Display.loader.gui_from_json import UniversalGuiLoader

# In a test script or temporary frame:
test_gui = UniversalGuiLoader(parent_frame, json_path="path/to/your_gui.json", config=app_config)
test_gui.pack(fill="both", expand=True)
```

For more details on specific widgets, refer to the documentation in `workers/builder/*/`.
