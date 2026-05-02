# oaGui/Documentation/coordinate_transformer.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for the geometry transformation engine.

## 🚀 Overview
The `CoordinateTransformer` is the mathematical engine for all UI transformations. It handles normalization, value-to-pixel mapping, and polar-to-cartesian rotations.

## 🏗️ Partitioned Architecture
- **Layer**: Interface (UI Partition)
- **Role**: Mathematical Transformation Engine 🧮

## 🚀 Native Acceleration
- **Rust Core**: Utilizes `oa_geometry_math_rs` for high-performance calculations. 🦀⚡
- **Fallback**: Includes robust pure-Python implementations for systems without native binaries. 🐍

## 🔧 Core Functions
### `normalize_value()`
- **Purpose**: Normalizes a value to a `0.0 - 1.0` range based on provided min/max bounds. 📏

### `value_to_pixel()`
- **Purpose**: Maps a normalized value to a physical pixel position within a given length. 📐

### `rotate_point()`
- **Purpose**: Rotates a 2D point around a center by a specific angle in degrees. 🔄

### `get_position()` / `get_angle()`
- **Purpose**: High-speed polar-to-cartesian conversions for rotary knobs and circular meters. 🧭
