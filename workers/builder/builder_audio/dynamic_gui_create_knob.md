# Dynamic GUI Knob Widget User Guide

This guide provides a comprehensive overview of the `_Knob` widget, implemented in `workers/builder/builder_audio/dynamic_gui_create_knob.py`. This widget renders a customizable, rotary knob using Tkinter's Canvas, suitable for audio applications and other control interfaces.

## 1. Overview

The `_Knob` widget is a versatile input control that mimics a physical rotary knob. It supports:
*   **Mouse Dragging:** Click and drag vertically to adjust the value.
*   **Mouse Wheel:** Scroll to increment/decrement the value.
*   **Keyboard Modifiers:** Hold `Ctrl` + `Alt` for fine-tuning.
*   **Manual Entry:** `Alt` + Click to open a text entry box for precise value input.
*   **Reset:** `Ctrl` + Click or Middle Click to jump to a reference point (default).
*   **Visual Feedback:** Customizable arc, pointer, and tick marks.
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

### Functional Behaviors
| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `infinity` | Boolean | `False` | If `true`, the knob wraps around from max to min (e.g., for phase 0-360). |
| `fine_pitch` | Boolean | `False` | If `true`, significantly reduces drag sensitivity for precise adjustments. |

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

## 4. Implementation Examples

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

### Pan Knob (Bipolar)
```json
"pan_knob": {
  "type": "_Knob",
  "label_active": "Pan",
  "min": -50.0,
  "max": 50.0,
  "value_default": 0.0,
  "reff_point": 0.0,
  "width": 50,
  "height": 50,
  "indicator_color": "#FFC107"
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

### Fine Tune Pitch
```json
"fine_tune": {
  "type": "_Knob",
  "label_active": "Fine Tune",
  "min": -100.0,
  "max": 100.0,
  "fine_pitch": true,
  "label_Text_position": "left",
  "indicator_color": "#E91E63"
}
```

## 5. Developer Implementation Details

The widget logic is encapsulated in `KnobCreatorMixin` within `dynamic_gui_create_knob.py`.

*   **`_create_knob`**: The factory method that parses the JSON configuration, sets up the `CustomKnobFrame`, handles layout (labels, canvas positioning), and binds events.
*   **`CustomKnobFrame`**: A `ttk.Frame` subclass that manages the logical state (`variable`), MQTT broadcasting (`state_mirror_engine`), and specialized actions like the manual entry popup (`_open_manual_entry`) and reset logic (`_jump_to_reff_point`).
*   **`_draw_knob`**: The rendering engine. It draws the background arc (secondary color), the active value arc (indicator color), the pointer line, ticks, and textual values on the Tkinter Canvas.
*   **Event Binding**: Uses `canvas.bind` for mouse interactions and `knob_value_var.trace_add` to trigger redraws whenever the value changes (whether from UI interaction or incoming MQTT messages).

---
*Generated for OPEN-AIR Project - 2026*
