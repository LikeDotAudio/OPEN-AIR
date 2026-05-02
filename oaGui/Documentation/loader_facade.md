# oaGui/Documentation/loader_facade.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for the GUI loading facade.

## 🚀 Overview
The `LoaderFacade` provides a unified interface for resource resolution and GUI instantiation. It abstracts the complexities of dynamic Python loading and widget orchestration.

## 🏗️ Partitioned Architecture
- **Layer**: FileReaders (UI Partition)
- **Role**: Resource Loading Facade 🏛️

## 🔧 Core Functions
### `load_and_instantiate_gui()`
- **Purpose**: Loads a UI from a path and builds it into a parent widget. 🏗️
- **Actions**: Resolves resources (JSON/PY) and delegates instantiation to the `create_gui_instance` atomic service.

### `load_module_from_path()`
- **Purpose**: Dynamically imports a Python module via the `LoaderPythonEngine`. 📂

### `instantiate_widget()`
- **Purpose**: Instantiates a specific widget class via the `WidgetInstantiator`. 🔨
