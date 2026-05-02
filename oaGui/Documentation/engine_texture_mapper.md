# oaGui/Documentation/engine_texture_mapper.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for background texture coordinate mapping.

## 🚀 Overview
The `EngineTextureMapper` handles the pixel-perfect mapping of global background textures to local widget coordinates. It ensures that transparent widgets correctly display a "slice" of the underlying panel patina.

## 🏗️ Partitioned Architecture
- **Layer**: Workers (UI Partition)
- **Role**: Texture Coordinate Aligner 📏

## 🔧 Core Functions
### `perform_slice()`
- **Purpose**: Calculates and applies the correct background texture slice to the widget's canvas. 🖼️
- **Mechanism**:
    1. Resolves the global background source and scroll reference.
    2. Calculates relative (x, y) coordinates.
    3. Crops the background image based on the widget's current geometry. ✂️
    4. Updates the widget's background color and canvas image. 🎨
- **Optimization**: Uses state-caching to avoid redundant cropping operations if geometry hasn't shifted. ⚡
