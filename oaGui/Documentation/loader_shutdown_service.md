# oaGui/Documentation/loader_shutdown_service.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for graceful system termination.

## 🚀 Overview
The `LoaderShutdownService` ensures a clean, sequential shutdown of all background services and UI components. It prioritizes data persistence and graceful resource release.

## 🏗️ Partitioned Architecture
- **Layer**: Managers (UI Partition)
- **Role**: Shutdown Orchestrator 🛑

## 🔧 Core Functions
### `on_closing()`
- **Purpose**: Gracefully terminates all UI and Communication sub-processes. 👋 [EXIT]
- **Actions**:
    1. Saves current window geometry (position/size). 💾
    2. Initiates a threaded shutdown of all managers to prevent UI hangs. ⚡
    3. Finalizes the log flush and quits the Tkinter mainloop.

### `shutdown()`
- **Purpose**: Synchronous shutdown for non-GUI-driven termination (e.g., SIGTERM or KeyboardInterrupt). 🛑
- **Side Effects**: Immediately signals all managers to stop and exits the process.

### `attach_to_root()`
- **Purpose**: Binds the `on_closing` routine to the window manager's `WM_DELETE_WINDOW` protocol. 🔗
