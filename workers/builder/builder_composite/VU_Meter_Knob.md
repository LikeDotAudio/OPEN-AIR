# VU Meter Knob Composite Widget

## Overview
The **VU Meter Knob** is a composite widget that combines a classic **Needle VU Meter** with a **Rotary Knob**. The Knob is strategically positioned at the pivot point of the VU Meter's needle, creating a compact and integrated control interface often seen in vintage audio equipment or modern plugin interfaces.

## Usage
To use this widget in your GUI layout JSON, specify the `widget_type` as `_VUMeterKnob`.

### JSON Configuration
The configuration is unique because it handles settings for both the VU Meter (background/needle) and the Knob (foreground control) within a single definition.

*   **VU Meter Settings:** Standard keys (like `min`, `max`, `path`, `size`) apply directly to the VU Meter.
*   **Knob Settings:** Keys prefixed with `knob_` are stripped of their prefix and passed to the Knob component. For example, `knob_min` becomes `min` for the knob, and `knob_path` becomes `path` for the knob.

### Key Parameters

#### General / VU Meter
*   **`widget_type`**: Must be `_VUMeterKnob`.
*   **`label_active`**: The label displayed for the entire composite widget.
*   **`path`**: The MQTT/Data path for the **VU Meter's** value (read-only indication).
*   **`size`**: The overall width of the VU Meter. The height is calculated automatically based on this.
*   **`min` / `max`**: The range for the VU Meter needle.
*   **`Meter_viewable_angle`**: The angle of the meter arc (e.g., 90, 180, 270).
*   **Ballistics**: `glide_time`, `fall_time`, `hold_time`, `dwell_time` control the needle's movement physics.
*   **Styling**: `Pointer_colour`, `Lower_range_colour`, `upper_range_Colour`.

#### Knob (Prefixed with `knob_`)
*   **`knob_path`**: The MQTT/Data path for the **Knob's** value (control input).
*   **`knob_min` / `knob_max`**: The range for the Knob control.
*   **`knob_width` / `knob_height`**: Dimensions of the knob.
*   **`knob_shape`**: The visual shape of the knob (e.g., `"circle"`, `"gear"`, `"octagon"`).
*   **`knob_pointer_style`**: The style of the indicator on the knob (e.g., `"line"`, `"triangle"`, `"notch"`).
*   **`knob_indicator_color`**: Color of the knob's pointer.
*   **`knob_outline_thickness`**: Thickness of the knob's border.
*   **`knob_teeth`**: Number of teeth if using the "gear" shape.

## How It Works
1.  **Config Splitting**: The builder receives one configuration dictionary. It creates a copy for the VU Meter and another for the Knob. It iterates through the keys; if a key starts with `knob_`, it is moved to the Knob's configuration (without the prefix).
2.  **VU Meter Creation**: It first builds the standard Needle VU Meter using the `NeedleVUMeterCreatorMixin`.
3.  **Pivot Calculation**: It identifies the canvas within the VU Meter and calculates the exact `(x, y)` coordinate of the needle's pivot point.
4.  **Knob Injection**: It creates the Knob widget using the `KnobCreatorMixin` and embeds it into the VU Meter's canvas specifically at the calculated pivot coordinates using `canvas.create_window`.
5.  **Smart Resizing**: If the Knob is large or the Meter Angle is wide (e.g., 270°), the component automatically calculates if the drawing extends beyond the standard canvas height and resizes the canvas to prevent clipping.

## Example Configuration

```json
{
  "Master_L": {
    "widget_type": "_VUMeterKnob",
    "label_active": "Master L",
    
    "comment": "--- VU Meter Settings ---",
    "path": "audio/master/left/vu",
    "size": 200,
    "min": -60,
    "max": 6,
    "Meter_viewable_angle": 90,
    
    "comment": "--- Knob Settings ---",
    "knob_path": "audio/master/left/gain",
    "knob_min": 0,
    "knob_max": 100,
    "knob_width": 100,
    "knob_height": 100,
    "knob_shape": "circle",
    "knob_pointer_style": "line",
    "knob_outline_thickness": 5
  }
}
```
