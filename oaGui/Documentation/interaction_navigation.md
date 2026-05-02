# oaGui/Documentation/interaction_navigation.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for UI section navigation logic.

## 🚀 Overview
The `InteractionNavigationMixin` handles specialized "jumps" between different sections of the UI, such as navigating directly to a specific instrument's control tab in the Splinker dashboard.

## 🏗️ Partitioned Architecture
- **Layer**: Managers (UI Partition)
- **Role**: Navigation Manager 🗺️

## 🔧 Core Functions
### `show_splinker_tab()`
- **Purpose**: Navigates the user to the Splinker interface. 🚀
- **Actions**:
    1. Resolves the physical frame path for the Splinker module.
    2. Selects the corresponding tab in the parent Notebook.
    3. Optionally injects pending topics (Source/Destination) into the Splinker dashboard once populated. 📡
