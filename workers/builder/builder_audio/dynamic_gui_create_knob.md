# Dynamic GUI Knob Widget User Guide

This guide provides a comprehensive overview of the `_Knob` widget, implemented in `workers/builder/builder_audio/dynamic_gui_create_knob.py`. This widget renders a highly customizable, rotary knob using Tkinter's Canvas, suitable for audio applications and other control interfaces.

## 1. Overview

The `_Knob` widget is a versatile input control that mimics a physical rotary knob. It supports:
*   **Mouse Dragging:** Click and drag vertically to adjust the value.
*   **Mouse Wheel:** Scroll to increment/decrement the value.
*   **Keyboard Modifiers:** Hold `Ctrl` + `Alt` for fine-tuning.
*   **Manual Entry:** `Alt` + Click to open a text entry box for precise value input.
*   **Reset:** `Ctrl` + Click or Middle Click to jump to a reference point (default).
*   **Visual Feedback:** Customizable shape (Circle, Octagon, Gear), arc, pointer styles, and tick marks.
*   **State Mirroring:** Integration with MQTT for real-time state synchronization.

## 2. JSON Configuration Parameters

To use the knob in your application, define it in your JSON layout configuration with the type `_Knob`. Below are the available parameters:

### Core Parameters
| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `type` | String | `_Knob` | **Required.** Specifies the widget type. |
| `label_active` | String | `""` | The text label displayed near the knob. |
| `path` | String | `None` | The unique identifier/path for MQTT state mirroring. |
| `min` | Float | `0.0` | The minimum value of the knob. |
| `max` | Float | `100.0` | The maximum value of the knob. |
| `value_default` | Float | `0.0` | The initial value of the knob. |
| `reff_point` | Float | `(min+max)/2` | The reference point value (e.g., center detent) to jump to on reset. |

### Visual Customization
| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `width` | Integer | `50` | The width of the knob canvas in pixels. |
| `height` | Integer | `50` | The height of the knob canvas in pixels. |
| `indicator_color` | Hex String | Theme Accent | The color of the active value arc and pointer (e.g., `#33A1FD`). |
| `show_label` | Boolean | `True` | Whether to display the `label_active` text. |
| `label_Text_position`| String | `"top"` | Position of the label relative to the knob: `"top"`, `"bottom"`, `"left"`, `"right"`. |
| `text_inside` | Boolean | `False` | If `true`, displays the current value number inside the knob center instead of below it. |
| `no_center` | Boolean | `False` | If `true`, hides the small center dot decoration. |

### Advanced Visuals (Ticks & Pointer)
| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `show_ticks` | Boolean | `False` | If `true`, draws tick marks around the knob. |
| `tick_length` | Integer | `10` | The length of the tick marks in pixels. |
| `arc_width` | Integer | `5` | The thickness of the value arc track. |
| `pointer_length` | Float/None | `None` | Custom length of the pointer line. If `None`, calculated dynamically based on radius. |
| `pointer_offset` | Integer | `0` | Distance from the center where the pointer line starts (useful for "floating" pointers). |
| `pointer_style` | String | `"line"` | Style of the pointer: `"line"`, `"triangle"`, `"notch"`. |
| `tick_style` | String | `"simple"` | Style of the ticks: `"simple"` (lines), `"numeric"` (numbers), `"dots"`. |

### Shape & Geometry (New in v20260114)
| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `shape` | String | `"circle"` | Base shape of the knob body: `"circle"`, `"octagon"`, `"gear"`. |
| `knob_fill_color` | Hex String | `""` (Empty) | Solid fill color for the knob body. If empty, it's transparent (or wireframe). |
| `knob_outline_color` | Hex String | Theme Secondary | Color of the knob shape outline. |
| `knob_outline_thickness`| Integer | `0` | Thickness of the knob shape outline. |
| `gradient_level` | Integer | `0` | Adds concentric rings to simulate a gradient (0-5). |
| `knob_teeth` | Integer | `8` | **For Gear Shape Only.** Sets the number of teeth on the gear. |

## 3. Interaction Guide

### Mouse Controls
*   **Left Click & Drag:** Adjusts the value. Dragging up increases, down decreases.
*   **Mouse Wheel:** Increments or decrements the value by ~5% of the range.
*   **Middle Click:** Resets the value to `reff_point`.
*   **Ctrl + Click:** Resets the value to `reff_point`.
*   **Alt + Click:** Opens a small text box to type a specific value manually. Press `Enter` to confirm or `Esc` to cancel.

### Precision Control
*   **Normal Drag:** Standard sensitivity (full range in ~200px drag).
*   **Fine Control (Ctrl+Alt+Drag):** Reduces sensitivity by half for finer adjustments.
*   **Fine Pitch Mode:** If `fine_pitch` is set to `true` in config, base sensitivity is 1/10th of normal.

## 4. Rendering Layering (Z-Order)
To ensure clarity and visual stacking, the knob is rendered in the following order (bottom to top):
1.  **Background Track:** The static arc representing the full range.
2.  **Ticks:** The scale indicators (dots, lines, or numbers).
3.  **Body (The Shape):** The main knob form (Gear, Circle, Octagon), including its fill and outline. This sits *on top* of the ticks.
4.  **Pointer:** The indicator (Line, Triangle, Notch) sits *on top* of the body.
5.  **Text:** If `text_inside` is active, the value text is rendered on the very top.

## 5. Implementation Examples

### Basic Volume Knob
```json
"volume_knob": {
  "type": "_Knob",
  "label_active": "Volume",
  "min": 0.0,
  "max": 100.0,
  "value_default": 75.0,
  "width": 60,
  "height": 60,
  "indicator_color": "#4CAF50"
}
```

### Solid Gear Knob
```json
"gear_knob": {
  "type": "_Knob",
  "label_active": "Gear",
  "width": 100,
  "height": 100,
  "shape": "gear",
  "knob_teeth": 12,
  "knob_fill_color": "#FF0000",
  "knob_outline_color": "white",
  "knob_outline_thickness": 2,
  "indicator_color": "white",
  "pointer_style": "triangle"
}
```

### Advanced Infinite Phase Knob
```json
"phase_knob": {
  "type": "_Knob",
  "label_active": "Phase",
  "min": 0.0,
  "max": 360.0,
  "infinity": true,
  "text_inside": true,
  "show_ticks": true,
  "tick_length": 5,
  "arc_width": 3,
  "indicator_color": "#9C27B0"
}
```

### Monochrome Wireframe
```json
"mono_knob": {
  "type": "_Knob",
  "label_active": "Mono",
  "width": 80,
  "height": 80,
  "shape": "gear",
  "knob_fill_color": "black",
  "knob_outline_color": "white",
  "knob_outline_thickness": 1,
  "indicator_color": "white",
  "pointer_style": "notch"
}
```

## 6. Developer Implementation Details

The widget logic is encapsulated in `KnobCreatorMixin` within `dynamic_gui_create_knob.py`.

*   **`_create_knob`**: The factory method that parses the JSON configuration, sets up the `CustomKnobFrame`, handles layout (labels, canvas positioning), and binds events.
*   **`CustomKnobFrame`**: A `ttk.Frame` subclass that manages the logical state (`variable`), MQTT broadcasting (`state_mirror_engine`), and specialized actions like the manual entry popup (`_open_manual_entry`) and reset logic (`_jump_to_reff_point`).
*   **`_draw_knob`**: The rendering engine. It orchestrates the drawing steps in a strict Z-order to ensure proper visual layering.
*   **`_draw_body`**: Handles the geometry generation for shapes (Circle, Octagon, Gear) and applies fills, outlines, and gradient rings.
*   **Event Binding**: Uses `canvas.bind` for mouse interactions and `knob_value_var.trace_add` to trigger redraws whenever the value changes (whether from UI interaction or incoming MQTT messages).

---
*Generated for OPEN-AIR Project - 2026*