# oaGui/Documentation/loader_python_engine.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for dynamic Python module loading.

## 🚀 Overview
The `LoaderPythonEngine` handles the dynamic importation of Python GUI modules. It scans imported modules for valid Tkinter-based classes or explicit factory functions.

## 🏗️ Partitioned Architecture
- **Layer**: Methods (UI Partition)
- **Role**: Dynamic Module Loader 📂🐍

## 🔧 Core Functions
### `load()`
- **Purpose**: Dynamically imports a module from a file path.
- **Discovery Logic**:
    1. Prioritizes modules that expose a `get_gui_class()` factory function. ✅
    2. Falls back to finding the first class that inherits from `tk.Frame` or `ttk.Frame`. 🔨
- **Side Effects**: Registers the module in `sys.modules` using a project-relative dot-notation path. 🔗
- **Outputs**: Returns the identified GUI class or `None`.
