# oaGui/Documentation/folder_layout_interpreter.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for directory intent interpretation.

## 🚀 Overview
The `FolderLayoutInterpreter` translates file paths and directory structures into physical UI layout intents. It uses a series of detectors to determine if a folder represents a Notebook, a PanedWindow, or a simple collection of GUI files.

## 🏗️ Partitioned Architecture
- **Layer**: FileReaders (UI Partition)
- **Role**: Layout Intent Interpreter 🧠📁

## 🔧 Core Functions
### `parse_directory()`
- **Purpose**: Determines the layout type and gathers data for a path.
- **Logic**: 
    1. Checks for a `layout.json` override. 📄
    2. If missing, scans directory contents using a rule-based detector sequence. 🔍

### `_parse_directory_listing()`
- **Purpose**: Infers layout type from directory contents (Rules).
- **Rules**:
    - **MultiWindow**: Multiple top-level folders. 🪟
    - **SplitPane**: Folder names matching `left_XX`, `top_XX`, etc. ✂️
    - **Notebook**: Folders with numeric prefixes (e.g. `1_Oscilloscope`). 📑

### `_scan_for_gui_files()`
- **Purpose**: Recursively checks if a folder contains valid GUI resources (.json or .py). 🔍
- **Optimization**: Uses a scan cache to avoid redundant FS hits. ⚡
