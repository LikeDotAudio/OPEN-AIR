# oaGui/Documentation/folder_recursive_scanner.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for recursive directory-based UI building.

## 🚀 Overview
The `FolderRecursiveScannerMixin` is responsible for traversing directory structures and building the corresponding UI hierarchy. It maps directory intents (Notebooks, Panes, etc.) to specialized layout builders.

## 🏗️ Partitioned Architecture
- **Layer**: FileReaders (UI Partition)
- **Role**: Structural Directory Scanner 📂🏗️

## 🔧 Core Functions
### `_build_from_directory()`
- **Purpose**: Recursively builds the GUI structure from a given path.
- **Phases**:
    1. Resolves layout information (Intent) for the path. 🔍
    2. Selects a specialized **Layout Builder** (e.g. Notebook, Split). 🛠️
    3. Triggers the build sequence.
- **Recursion**: Builders may call back into the scanner for nested structures. 🔄

### `_initialize_layout_builders()`
- **Purpose**: Registry of available layout builder instances (MultiWindow, Notebook, Split, etc.). 📋
