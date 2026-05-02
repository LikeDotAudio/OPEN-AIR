# oaGui/Documentation/tab_window_manager.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for tear-off tab window management.

## 🚀 Overview
The `TabWindowManager` handles the "liberation" and "re-attachment" of Notebook tabs into independent Toplevel windows, allowing for flexible workspace layouts.

## 🏗️ Partitioned Architecture
- **Layer**: Managers (UI Partition)
- **Role**: Window & Tear-off Manager 🪟

## 🔧 Core Functions
### `tear_off_tab()`
- **Purpose**: Liberates a tab from its parent Notebook into a standalone window. 🕊️
- **Delegation**: Uses `liberate_notebook_tab` atomic service.

### `_on_tear_off_window_close()`
- **Purpose**: Handles the closing of a torn-off window by re-attaching the tab to its original Notebook. 🔗
- **Delegation**: Uses `re_attach_liberated_tab` atomic service.
