# FaderDial — fader + dial composite

The `_Horizontal_with_dial_Value` composite: a horizontal fader (whole-number
part) plus a rotary knob (decimal part) plus a value readout, summing to one
number. Fluid when given a `%` width; redraws crisply with no jiggle.

- **Defines (global):** `FaderDial`
- **Props:** `value`, `onChange`, `config` (min/max under `domain.primary` *or* top-level strings)
- **Loaded by:** the live app via `frontEnd/Core/Launch/index.html`.

<!-- wysiwyg:sample (auto-generated from oaGuiElements; edit here to drive the library) -->
## Sample (WYSIWYG library source)

The WYSIWYG editor builds this widget's **palette entry, live preview, and
property manipulators** from the JSON block below. The web server
(`frontEnd/Core/Launch/LauchWebserver.py` → `get_grab_bag()`) scans these
READMEs, extracts this block, and serves it at `/api/grabbag`. `_README`
documents the widget; every `_LEGEND` array becomes a dropdown of allowed values
in the property editor.

```json
{
  "Exhaustive_Composite_Example": {
    "type": "_Horizontal_with_dial_Value",
    "column_spacing": [
      80,
      10,
      10
    ],
    "label_active": "Master High-Precision Tuning",
    "description": "An exhaustive sample demonstrating every possible sub-configuration for the OcaCompositeFaderKnob.",
    "layout": {
      "width": 600,
      "height": 120,
      "stretch": "width",
      "padx": 20,
      "pady": 10,
      "sticky": "ew"
    },
    "min": 0.0,
    "max": 5000.0,
    "default_value": 1250.0,
    "step_coarse": 100.0,
    "step_fine": 0.001,
    "units": "MHz",
    "show_label": true,
    "value_config": {
      "_README": "Overrides for the numerical entry and unit readout panel (Column 2).",
      "width": 12,
      "font": 18,
      "colour": "#00FF00",
      "bg_color": "#050505",
      "height": 35
    },
    "fader_config": {
      "_README": "Deep overrides for the coarse adjustment horizontal fader (Column 0).",
      "tick_interval": 500,
      "show_ticks": true,
      "bar_color": "#222222",
      "active_color": "#FF9900",
      "glow_intensity": 1.8,
      "cap_color": "#dcdcdc",
      "cap_highlight_color": "#33A1FD",
      "fader_cap_scale": 1.2,
      "cap_width": 55,
      "cap_height": 40,
      "value_highlight_color": "#FF9900",
      "tick_color": "#888888",
      "sub_tick_color": "#444444",
      "log_exponent": 1.0,
      "reff_point": 2500.0
    },
    "dial_config": {
      "_README": "Deep overrides for the fine-tuning rotary dial (Column 1).",
      "knob_style": "vintage",
      "shape": "gear",
      "knob_teeth": 12,
      "width": 80,
      "height": 80,
      "active_color": "#00ffff",
      "bg_color": "#2b2b2b",
      "indicator_color": "#00ffff",
      "pointer_style": "triangle",
      "pointer_length": 25,
      "pointer_offset": 5,
      "gradient_level": 3,
      "knob_fill_color": "#333333",
      "knob_outline_thickness": 1,
      "knob_outline_color": "#555555",
      "show_ticks": true,
      "tick_style": "dots",
      "tick_length": 8,
      "arc_width": 6,
      "text_inside": false,
      "no_center": false,
      "label_Text_position": "top",
      "infinity": true,
      "fine_pitch": true
    },
    "yak_handler": {
      "_README": "Hardware bridge configuration for MQTT/SCPI communication.",
      "enable": true,
      "yak_type": "set",
      "sub_path": "Frequency",
      "command": "Set_Freq",
      "input_name": "hz_value",
      "converter": "mhz_to_hz"
    },
    "cosmetics": {
      "_README": "Legacy fallback color definitions used if specific configs are missing.",
      "colors": {
        "primary": "#FF9900",
        "secondary": "#444444",
        "background": "#2b2b2b"
      }
    }
  },
  "_README": "This sample is REALLY REALLY complete. It outlines every sub-config breakout for the fader, knob, and value elements, including style options and hardware handlers.",
  "_LEGEND": {
    "knob_styles": [
      "standard",
      "panner",
      "dial",
      "vintage",
      "industrial",
      "modern"
    ],
    "knob_shapes": [
      "circle",
      "octagon",
      "gear"
    ],
    "pointer_styles": [
      "line",
      "triangle",
      "notch"
    ],
    "tick_styles": [
      "simple",
      "dots",
      "numeric"
    ],
    "column_spacing_note": "[Fader_Width, Knob_Width, Value_Width] - Percentages should sum to 100."
  }
}
```
