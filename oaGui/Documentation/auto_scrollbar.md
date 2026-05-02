# oaGui/Documentation/auto_scrollbar.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for auto-hiding industrial scrollbars.

## 🚀 Overview
The `AutoScrollbar` is a specialized Tkinter scrollbar that automatically manages its own visibility. It is designed for industrial UIs where screen real estate is at a premium.

## 🏗️ Partitioned Architecture
- **Layer**: Interface (UI Partition)
- **Role**: Intelligent UI Component ↕️

## 🔧 Core Functions
### `set()`
- **Purpose**: Overrides the standard `set` method to check content scale.
- **Logic**: If the content fits entirely within the viewport (lo=0.0, hi=1.0), the scrollbar physically removes itself from the grid. 👻
- **Action**: Automatically re-grids itself if the content grows beyond the viewport. 👁️
