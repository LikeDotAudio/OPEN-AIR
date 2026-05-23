# Knob — rotary knob

Rotary control built with separated concerns: motion/angle logic, tick scale,
and the 3D cap body.

- **Defines (globals):** `Knob` (orchestrator), `KnobCap`, `KnobTicks`,
  `getKnobAngles`, `describeArc`, `polarToCartesian`
- **Props:** `value`, `onChange`, `config` (domain + cosmetics)
- **Loaded by:** the live app via `frontEnd/Core/Launch/index.html`.
- **Demo:** open `../index.html`.

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
  "Exhaustive_Knob_Example": {
    "type": "_SmartKnob",
    "identity": {
      "label": "Master Tuning",
      "id": "tuning_knob_01",
      "notes": "A ultra-complete example of the photorealistic rotary control."
    },
    "geometry": {
      "width": 200,
      "height": 250,
      "padding": 10,
      "stretch": "none",
      "anchor": "center",
      "align": "center"
    },
    "domain": {
      "primary": {
        "min": 0.0,
        "max": 1000.0,
        "value_default": 500.0,
        "unit": "MHz",
        "zero_point": 0.0,
        "step": 0.1,
        "law": "linear"
      },
      "rotation": {
        "value": 500.0
      }
    },
    "dynamics": {
      "fps_limit": 60,
      "smoothing": 0.1,
      "retention": 500,
      "attack_ms": 50,
      "release_ms": 300,
      "ballistics": "vu",
      "path": "System/DSP/Oscillator/Freq"
    },
    "cosmetics": {
      "visualization": "dial",
      "colors": {
        "primary": "#33A1FD",
        "secondary": "#444444",
        "alert": "#FF0000",
        "warning": "#FFA500",
        "background": "#2b2b2b",
        "highlight": "#FFFFFF",
        "active": "#00FF00"
      },
      "style_flags": {
        "show_grid": true,
        "fill_shape": true
      },
      "pointer": {
        "show": true,
        "style": "triangle",
        "length": 30,
        "offset": 5,
        "thickness": 2,
        "primary_color": "#33A1FD",
        "secondary_color": "#0055AA",
        "pivot_size": 8,
        "pivot_color": "#222222",
        "pivot_crop": true
      },
      "scale": {
        "show": true,
        "style": "dots",
        "length": 12,
        "thickness": 1,
        "size": 10,
        "upper_range": 800.0
      },
      "styling": {
        "gradient": 3,
        "teeth": 12,
        "outline_thickness": 1,
        "outline_color": "#555555",
        "fill_color": "#1a1a1a",
        "arc_width": 6,
        "no_center": false,
        "cap_radius": 40,
        "cap_color": "#333333"
      },
      "style_overrides": {
        "knob_style": "vintage",
        "shape": "gear"
      }
    },
    "readout": {
      "show_value": true,
      "location": "bottom",
      "units": "MHz",
      "decimal_places": 2,
      "text_inside": false,
      "font_size": 10,
      "label_position": "top"
    },
    "interaction": {
      "sensitivity": 1.0,
      "scroll_enabled": true,
      "infinity": true,
      "fine_pitch": true,
      "delta_absolute": false,
      "freestyle": false,
      "is_read_only": false
    },
    "layout": {
      "sticky": "nsew",
      "padx": 10,
      "pady": 10,
      "weight": 1
    }
  },
  "_README": "This sample is REALLY REALLY COMPLETE. It follows the 5-pillar 'Universal Rhyme' schema (Identity, Geometry, Domain, Dynamics, Cosmetics) plus Readout, Interaction, and Layout. Every supported sub-parameter is outlined here for use in the WYSIWYG editor or manual JSON construction.",
  "_LEGEND": {
    "visualization_types": [
      "circle",
      "octagon",
      "gear",
      "dial",
      "panner"
    ],
    "knob_styles": [
      "standard",
      "panner",
      "dial",
      "vintage",
      "industrial",
      "modern"
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
    "laws": [
      "linear",
      "log"
    ],
    "ballistics": [
      "vu",
      "ppm",
      "fast",
      "slow"
    ],
    "label_positions": [
      "top",
      "bottom",
      "left",
      "right"
    ]
  }
}
```
