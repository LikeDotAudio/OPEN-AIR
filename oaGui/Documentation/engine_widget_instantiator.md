# oaGui/Documentation/engine_widget_instantiator.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for GUI widget instantiation.

## 🚀 Overview
The `WidgetInstantiator` handles the physical instantiation of Python-based GUI classes and their integration into the managed layout tree. It wraps individual modules in a `LoaderOrchestrator` for consistent lifecycle management.

## 🏗️ Partitioned Architecture
- **Layer**: Managers (UI Partition)
- **Role**: Widget Instantiator 🔨

## 🔧 Core Functions
### `instantiate()`
- **Purpose**: Dynamically instantiates a widget class and anchors it in the UI. 🏗️
- **Actions**:
    1. Prepares a standardized configuration dictionary.
    2. Wraps the widget in a `LoaderOrchestrator` (Hull).
    3. Manages geometric attachment (Pack or Grid) based on the parent's state. 🛠️
- **Outputs**: Returns the `LoaderOrchestrator` instance managing the widget.
