# oaGuiEditorWYSIWYG/Documentation/wysiwyg_editor.md
#
# High-level overview of the Modular WYSIWYG Definition Builder.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Version 20260417.0100.1
#
# Description: The primary landing page for the WYSIWYG module documentation.

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
`oaGuiEditorWYSIWYG/Entry.py`

The **oaGuiEditorWYSIWYG** module is the high-performance design environment 
for the OPEN-AIR ecosystem. It provides an interactive, pixel-perfect 
workspace for constructing industrial GUI definitions that are 
instantly compatible with the high-speed rendering engine.

## 🏗️ Partitioned Architecture (Core vs UI)
The module is strictly divided into two distinct layers:

### 🧠 Core (The Brain)
*   **StateManager**: The sole source of truth. Handles JSON manipulation 
    and maintains the state of the GUI being built.
*   **Event Bus Integration**: Communicates via the `oaComBroker` to ensure 
    loose coupling between UI actions and state changes.

### 🎨 UI (The Stage)
*   **InteractiveLayout**: The primary render area utilizing a 
    "Skeleton-First" rendering strategy.
*   **Overlays**: High-speed interaction layers for selection, sizing, 
    and alignment that bypass the standard widget event loop.
*   **Tabs**: Modular workspaces (Structure, Code, Library, Properties) 
    that provide specialized views of the central state.

## ⚙️ Operational Mandates
*   **Widget Registry**: All UI elements MUST be registered via the 
    `WidgetRegistry` to be discoverable by the Grab Bag and Renderer.
*   **Path-Based Sync**: Widgets are addressed via dot-notated paths 
    (e.g., `elements.main_panel.fader_1`).
*   **Ghost Mode**: Structural changes are validated in a low-overhead 
    "Ghost" render tier before high-res assets are generated.

## 🗺️ Documentation Map
*   [Architectural Narrative](./ARCHITECTURE.md) - The "How and Why"
*   [Interactive Layout](./interactive_layout.md) - The rendering engine
*   [Element Properties](./element_properties.md) - Property editing logic
*   [State Management](./state.md) - Core data synchronization
*   [Summary Map](./Summary.md) - Narrative folder synthesis
