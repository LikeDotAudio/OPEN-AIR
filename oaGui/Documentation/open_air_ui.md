# 🏷️ Open Air UI

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
`managers/Display/open_air_ui.py`

The **Dynamic UI Partition** for OPEN-AIR. This module orchestrates the entire graphical environment, handling GUI rendering, state mirroring, and user interaction. It is architecturally decoupled from the **System Core** and communicates via MQTT, ensuring that UI crashes or hangs do not compromise hardware safety or data logging.

### The Dynamic GUI Building Process
OPEN-AIR utilizes a "Filesystem-as-Architecture" approach, where the structure of the `oaGui/Assets/` directory directly dictates the layout and hierarchy of the user interface.

#### Process Flowchart
```text
[ oaGui/Assets/ Root ]
       |
       v
+-----------------+      +-----------------------+
|  LayoutParser   | <--- |   Folder Conventions  |
+-----------------+      | (left_, 1_Setup, etc) |
       |                 +-----------------------+
       v
+-----------------------+
| Recursive Container   |
| (Panes, Tabs, Grids)  |
+-----------------------+
       |
       |----[ Leaf Node: gui_*.py ]----> [ ModuleLoader ] 
       |                                       |
       |----[ Leaf Node: gui_*.json ]---> [ DynamicGuiBuilder ]
                                               |
                                               v
                                     +-----------------------+
                                     |    BlueprintLoader    |
                                     | (Merge Default Panel) |
                                     +-----------------------+
                                               |
                                               v
                                     +-----------------------+
                                     |  WidgetSchemaNormalizer|
                                     +-----------------------+
                                               |
                                               v
                                     +-----------------------+
                                     |    Widget Factory     |
                                     | (Registry & Injection)|
                                     +-----------------------+
                                               |
       +---------------------------------------+
       |
       v
+-----------------------+      +-----------------------+
|  StateMirrorEngine    | <--- |     MQTT Broker       |
| (Topic Registration)  | ---> | (Initial Publication) |
+-----------------------+      +-----------------------+
       |
       v
+-----------------------+
|     Settle Phase      |
| (Transparency/Resize) |
+-----------------------+
       |
       v
[   FINAL UI REVEAL     ]
```

#### 1. Bootstrap & Ignition
The lifecycle begins in `open_air_ui.py`. After initializing the Tkinter environment and showing the `SplashScreen`, control is handed to the `AsyncBootstrapEngine`. This engine initializes asynchronous communication services (MQTT, State Cache, Mirror Engine) before launching the main `Application` class.

#### 2. Architectural Discovery (Directory Crawling)
The `Application` class (found in `gui_display.py`) initiates a recursive build starting from the `oaGui/Assets/` root. This process is managed by the `DirectoryBuilderMixin`.
- **Crawl & Scan:** The system walks the directory tree.
- **Layout Parsing:** The `LayoutParser` analyzes folder names and `layout.json` files to determine the structural container for each branch.

#### 3. Layout Determination & Naming Conventions
Layouts are determined by specific naming conventions or explicit configuration:
- **Split Panes:** Folders prefixed with `left_`, `right_`, `top_`, or `bottom_` (e.g., `left_50`) are parsed as `ttk.PanedWindow` panels with defined weights.
- **Notebooks:** Folders with a numerical prefix (e.g., `1_Setup`, `2_Analysis`) are rendered as tabs within a `ttk.Notebook`.
- **Explicit Layouts:** A `layout.json` file can override these conventions to define complex nested grids or specific recursive build patterns.

#### 4. Module Ingestion & Loading
When the crawler reaches a "leaf" file (the actual GUI content), the `ModuleLoader` takes over:
- **Pure Python (`gui_*.py`):** These modules are dynamically imported and instantiated. They allow for complex, custom-coded interactive panels.
- **JSON Blueprints (`gui_*.json`):** These are passed to the `UniversalGuiLoader`, which instantiates a `DynamicGuiBuilder`.

#### 5. Dynamic Generation (JSON-based)
For JSON-based GUIs, the `DynamicGuiBuilder` performs a multi-stage transformation:
- **Ingestion:** `BlueprintLoader` reads the JSON using high-speed `orjson`.
- **Merging:** The specific GUI config is merged with `managers/Display/default_panel.json` to ensure consistent industrial styling and default behaviors.
- **Normalization:** The `WidgetSchemaNormalizer` flattens the tree, resolving geometry and cosmetic defaults.
- **Batch Building:** The `GuiBatchBuilderMixin` processes fields in batches to prevent UI blocking, instantiating widgets via the `WidgetRegistry` and `GuiWidgetFactoryMixin`.

#### 6. Widget Factory & MQTT Binding
The `WidgetRegistry` scans the `workers/builder/widgets/` directory at startup to discover available components (knobs, meters, buttons). As widgets are created:
- **Instantiation:** The factory maps JSON "type" keys to Python classes.
- **State Mirroring:** If a widget defines a `topic`, it is automatically bound to the `StateMirrorEngine`. This creates a bi-directional link between the UI element and the MQTT broker.

#### 7. The "Settle" Phase
Once the hierarchy is constructed, the `_rebuild_gui` logic ensures the interface settles:
- **Geometry Finalization:** Tkinter geometry managers are given time to calculate final sizes.
- **Transparency Reslicing:** Transparent overlays (via `TransparencyMixin`) are recalculated and applied to match the final widget positions.
- **Reveal:** The main window is finalized and revealed to the user.

## ⚙️ Assumptions & Constraints
- **MQTT Dependency:** The UI assumes a running MQTT broker for all state synchronization.
- **Decoupled Memory:** The UI partition cannot access Core memory directly; it relies entirely on the `StateRegistry` and MQTT topic updates.
- **Python 3.10+:** Utilizes modern typing and performance optimizations like `orjson`.

## 📚 API Reference

### Global Functions
#### `main()`
The entry point for the UI partition. Initializes environment paths, logging, and starts the Tkinter mainloop.

#### `_reveal_main_window(root, splash)`
Calculates the final window geometry, destroys the splash screen, and reveals the main application window.

**Parameters:**
- `root`: The Tkinter root window instance.
- `splash`: The SplashScreen instance to be destroyed.

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
