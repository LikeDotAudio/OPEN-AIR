# oaGui/Documentation/interaction_view_states.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for UI visibility group management.

## 🚀 Overview
The `InteractionViewStates` manager handles visibility groups, allowing multiple UI sections (e.g. collapsible blocks) to be toggled simultaneously via a right-click context menu.

## 🏗️ Partitioned Architecture
- **Layer**: Managers (UI Partition)
- **Role**: View State Manager 👁️

## 🔧 Core Functions
### `register()`
- **Purpose**: Registers a widget into a named visibility group. 📝
- **Actions**: Automatically adds a checkbutton to the master toggle menu.

### `_toggle_group()`
- **Purpose**: Toggles the visibility state of all widgets in a group. 🔄
- **Actions**: Calls `set_view_state("expanded"|"collapsed")` on each registered widget.

### `show_menu()`
- **Purpose**: Displays the visibility toggle context menu at the cursor position. 🖱️
