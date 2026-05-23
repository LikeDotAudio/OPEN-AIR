# NeedleMeter — analog needle meter

Analog VU-style needle meter with ballistics and high-fidelity bezel shapes.

- **Defines (globals):** `NeedleMeter`, `BEZEL_CONFIGS`, `getBezelPath`, `useNeedleBallistics`
- **Props:** `value`, `config` (min/max, bezel, cosmetics)
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
  "Exhaustive_Needle_Example": {
    "type": "_NeedleVUMeter",
    "identity": {
      "label": "Master Output",
      "id": "master_vu",
      "notes": "A vintage-style photorealistic needle meter with Next-Gen bezel support."
    },
    "geometry": {
      "width": 300,
      "height": 250,
      "size": 250,
      "scale_padding": 40,
      "pivot_offset_x": 0,
      "pivot_offset_y": 0,
      "stretch": "none"
    },
    "domain": {
      "primary": {
        "min": -20.0,
        "max": 3.0,
        "value_default": -20.0,
        "unit": "VU",
        "mid_range_start": -3.0,
        "red_zone_start": 0.0
      }
    },
    "dynamics": {
      "fps_limit": 60,
      "smoothing": 0.15,
      "ballistics": "vu",
      "peak_hold_ms": 2000,
      "path": "MasterBus/Metering/Output"
    },
    "cosmetics": {
      "colors": {
        "primary": "#FF9900",
        "secondary": "#444444",
        "background": "#2b2b2b",
        "pointer": "#CC0000",
        "pivot": "#222222",
        "lower": "#FFFFFF",
        "middle": "#FF9900",
        "upper": "#FF0000"
      },
      "style_flags": {
        "show_label": true,
        "ticks_visible": true,
        "scale_numbers": true,
        "peak_flag": true
      },
      "style_overrides": {
        "bezel_shape": "gem",
        "bezel_width": 12,
        "lighting_effects": true,
        "glass_reflection": true,
        "aperture_mask": "smile",
        "overlay_type": "dome"
      },
      "scale": {
        "viewable_angle": 90,
        "center_angle": 90,
        "tick_step": 1.0,
        "sub_ticks": 4,
        "tick_radius_offset": 5,
        "label_radius_offset": 20
      }
    },
    "interaction": {
      "is_read_only": true
    },
    "layout": {
      "sticky": "center",
      "padx": 10,
      "pady": 10
    }
  },
  "_README": "This sample is REALLY REALLY COMPLETE. It outlines the complex visual parameters for the vintage needle meter, including the 'Next-Gen' bezel geometries and ballistic physics.",
  "_LEGEND": {
    "meter_modes": [
      "mono",
      "stereo"
    ],
    "bezel_shapes": [
      "gem",
      "pyramid",
      "cylinder",
      "hex",
      "squircle",
      "badge",
      "crest",
      "octagon"
    ],
    "aperture_masks": [
      "smile",
      "frown",
      "straight"
    ],
    "overlay_types": [
      "dome",
      "flat"
    ],
    "ballistics": [
      "vu",
      "ppm",
      "fast",
      "slow"
    ],
    "pointer_styles": [
      "thin",
      "tapered",
      "vintage",
      "block"
    ]
  }
}
```
