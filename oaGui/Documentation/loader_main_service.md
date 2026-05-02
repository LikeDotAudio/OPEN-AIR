# oaGui/Documentation/loader_main_service.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for the main UI service orchestrator.

## 🚀 Overview
The `loader_main_service.py` is the primary entry point for the **UI Partition**. It orchestrates the entire lifecycle of the OPEN-AIR UI, coordinating high-level managers for windowing, composition, and shutdown while maintaining strict isolation from the hardware-focused Core Partition.

## 🏗️ Partitioned Architecture
- **Layer**: Managers (UI Partition)
- **Role**: Main Service Orchestrator 🖥️🎨

## 🔧 Core Functions
### `main()`
- **Purpose**: Main orchestration routine for the OPEN-AIR UI subsystem.
- **Phases**:
    1. **Environment Initialization**: Sets up paths, logging (UI partition), and global configuration. 📁
    2. **Window Creation**: Initializes the Tkinter root window and displays the splash screen. 🖼️
    3. **Service Composition**: Builds the dependency graph using the `LoaderServiceComposer`. 🏗️
    4. **System Coordination**: Attaches shutdown handlers and initiates periodic resource garbage collection. 🛡️
    5. **Bootstrapping**: Launches the `LoaderBootstrapEngine` in a background thread and enters the Tkinter mainloop. 🚀
- **Side Effects**: Spawns background threads, modifies global signal handlers, and opens the graphical window.

## 📡 Interactions
- **Inbound**: Reads global configuration via `oaConfigurationManager`. 📡📥📥
- **Outbound**: Manages lifecycle events and system status. 📡📤📤
