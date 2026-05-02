# oaGui/Documentation/engine_visual_effects.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for industrial transparency effects.

## 🚀 Overview
The `EngineVisualEffects` orchestrates the application of transparency and background slicing to widgets. It ensures that the UI maintains a cohesive "Industrial" look through procedural patina and texture mapping.

## 🏗️ Partitioned Architecture
- **Layer**: Workers (UI Partition)
- **Role**: Visual Effects Engine 🎨

## 🔧 Core Functions
### `apply_transparency()`
- **Purpose**: Entry point for applying transparency effects to a widget.
- **Actions**:
    1. Checks the **Render Tier** (bypasses effects in Fast/Ghost modes). 🏎️
    2. Parses the transparency configuration.
    3. Registers the widget for background slicing via the `EngineTextureMapper`. 🔗

### `cleanup()`
- **Purpose**: Clears the slicing registry and triggers garbage collection to prevent memory leaks during UI rebuilds. 🧹
