# oaGui/Documentation/Canvas_Viewport_Manager.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for the canvas viewport manager.

## 🚀 Overview
The `CanvasViewportManager` orchestrates the sizing and filling behavior of the GUI's primary drawing surface. It ensures that the inner build frame correctly expands to fill the viewport or activates scrolling when content exceeds physical dimensions.

## 🏗️ Partitioned Architecture
- **Layer**: Interface (UI Partition)
- **Role**: Viewport Controller 📏🔳

## 🔧 Core Functions
### `synchronize_to_viewport()`
- **Purpose**: Calculates and applies target dimensions for the content frame.
- **Logic**:
    - If horizontal scroll is disabled, the content frame is forced to the viewport width. ↔️
    - The height is always set to the maximum of the viewport or requested content height. ↕️
- **Side Effects**: Updates the canvas `scrollregion` to match the new content bounds. 🛠️

### `reset_view()`
- **Purpose**: Snaps the viewport back to the top-left (0,0) position. ↖️
