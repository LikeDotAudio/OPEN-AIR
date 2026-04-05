# 🏷️ Meter Config

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
The `MeterConfig` class provides a structured way to handle the complex configuration requirements for graphical meters within the OPEN-AIR system. It acts as a data bridge between raw JSON/blueprint definitions and the specialized rendering engines (e.g., `oaNeedleEngine_rs`).

### Primary Responsibilities
- **Data Parsing**: Converts raw configuration dictionaries into typed attributes.
- **Normalization**: Ensures consistent units for ballistics (timing), geometry (offsets), and visual styling (colors).
- **Default Resolution**: Provides sensible defaults for missing configuration keys.

---

## ⚙️ Assumptions & Constraints
- **Format**: Expects data structured for `MeterConfig` as defined in standard widget blueprints.
- **Dependencies**: Interacts with `oaStyle` for theme-aware color resolution.
- **Threading**: The configuration object is intended to be read-only after initialization.

---

## 📚 API Reference
For a complete list of classes, methods, and properties, please refer to the detailed reference file:

👉 **[Meter Config API Reference](./references/meter_config_api.md)**

---

## 📝 Focus on Intent
- **Geometry**: The meter uses a polar coordinate system for its scale. `meter_viewable_angle` and `meter_center_angle` are used to map linear values to rotational arc positions.
- **Ballistics**: Timing values (glide, dwell, fall) are critical for simulating physical meter behavior (VU/PPM).
- **Sub-tick Rendering**: Designed to support custom visual styles for analog-style dial precision.
