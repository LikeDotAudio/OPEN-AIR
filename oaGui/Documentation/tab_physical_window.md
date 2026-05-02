# oaGui/Documentation/tab_physical_window.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for the physical root window manager.

## 🚀 Overview
The `TabWindowManager` (in `Interface`) manages the creation, styling, and geometry restoration of the main Tkinter root window. It ensures a consistent "Industrial" aesthetic and handles OS-specific window state logic.

## 🏗️ Partitioned Architecture
- **Layer**: Interface (UI Partition)
- **Role**: Physical Window Manager 🪟

## 🔧 Core Functions
### `create_root_window()`
- **Purpose**: Initializes the `tk.Tk` root instance. 🚀
- **Actions**:
    1. Configures global style defaults (Dark Theme). 🎨
    2. Enforces a minimum window size of 800x600. 📏
    3. Restores previous session geometry from the layout cache. 💾
    4. Attaches a critical exception logger to the Tkinter callback system. 🛡️

### `reveal_main_window()`
- **Purpose**: Dismisses the splash screen and physically displays the main window. 👁️
- **Actions**: Handles OS-specific maximization (`-zoomed` on Linux).

### `save_window_geometry()`
- **Purpose**: Persists the current window size and position to the layout cache on exit. 💾
