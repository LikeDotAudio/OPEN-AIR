# Fader — standalone fader (demo)

High-fidelity single fader that infers orientation from its geometry and can
bind to MQTT.

- **Defines (globals):** `Fader`, `clamp`
- **Props:** `value`, `onChange`, `config`, `topic`, `nodeJson`
- **Demo:** open `../index.html`.

> **Note:** the live app does **not** load this file — it uses the production
> fader at `../core/Fader.jsx` (built from `core/Cap.jsx`, `core/Scale.jsx`,
> `core/utils.js`). This copy is the self-contained demo/standalone variant.

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
  "Exhaustive_Fader_Example": {
    "type": "_SmartFader",
    "identity": {
      "label": "Channel 1 Level",
      "id": "ch1_fader",
      "notes": "A ultra-complete example of the photorealistic vertical fader."
    },
    "geometry": {
      "width": 100,
      "height": 300,
      "padding": 5,
      "stretch": "height",
      "anchor": "center",
      "align": "center",
      "cap": {
        "w": 45,
        "h": 60
      }
    },
    "domain": {
      "primary": {
        "min": -100.0,
        "max": 12.0,
        "value_default": 0.0,
        "unit": "dB",
        "zero_point": 0.0,
        "law": "log",
        "log_exponent": 2.0
      },
      "linear": {
        "min": 0.0,
        "max": 1.0,
        "value": 0.75
      }
    },
    "dynamics": {
      "fps_limit": 60,
      "smoothing": 0.05,
      "path": "MixingConsole/Channels/1/Fader"
    },
    "cosmetics": {
      "colors": {
        "primary": "#33A1FD",
        "secondary": "#222222",
        "background": "#2b2b2b",
        "cap": "#dcdcdc",
        "cap_highlight": "#FF9900",
        "tick_color": "#888888",
        "sub_tick_color": "#444444",
        "highlight": "#FF9900"
      },
      "style_flags": {
        "show_grid": true,
        "show_label": true,
        "value_follow": true
      },
      "scale": {
        "show": true,
        "style": "simple",
        "interval": 10.0,
        "size": 0.4,
        "thickness": 1
      },
      "styling": {
        "glow_intensity": 1.5,
        "track_hover_color": "#333333",
        "fader_track_color": "#111111",
        "border_width": 0,
        "border_color": "#000000"
      }
    },
    "readout": {
      "show_value": true,
      "show_units": true,
      "units": "dB",
      "location": "bottom",
      "decimal_places": 1,
      "label_position": "top",
      "movement_value_display": true
    },
    "interaction": {
      "scroll_enabled": true,
      "is_read_only": false,
      "reff_point": 0.0
    },
    "layout": {
      "sticky": "ns",
      "padx": 10,
      "pady": 10,
      "weight": 1
    }
  },
  "_README": "This sample is REALLY REALLY COMPLETE. It follows the 5-pillar 'Universal Rhyme' schema (Identity, Geometry, Domain, Dynamics, Cosmetics) plus Readout, Interaction, and Layout.",
  "_LEGEND": {
    "fader_types": [
      "_Fader",
      "_SmartFader",
      "_CustomFader"
    ],
    "laws": [
      "linear",
      "log"
    ],
    "tick_label_positions": [
      "left",
      "right"
    ],
    "unit_positions": [
      "left",
      "right"
    ],
    "cap_dimensions": "Defined in geometry.cap.w/h or top-level cap_width/height.",
    "mouse_actions": "Middle-click resets to reff_point. Alt-click opens manual entry."
  }
}
```
