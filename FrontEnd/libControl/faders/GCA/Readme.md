# GCA — Ganged Controlled Array

Multi-channel ganged fader array with macro (master) and micro (per-channel)
modes, drawn on a canvas. Mirrors `oaGuiElements/Core/faders/fader_ganged_controlled_array`.

- **Defines (global):** `GCA`
- **Props:** `config`, `value`, `onChange`
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
  "horizontal_with_dial_Example": {
    "type": "_Horizontal_with_dial_Value",
    "label": {
      "active": {
        "text": {
          "En": "Tuning",
          "Fr": "Accord",
          "De": "Abstimmung",
          "Es": "Sintonía"
        },
        "text_size": 12,
        "text_color": "#cccccc"
      }
    },
    "layout": {
      "width": "100%",
      "height": 90,
      "stretch": "width",
      "font": 14,
      "padx": 10
    },
    "domain": {
      "locked": false,
      "min": "0",
      "max": "1000",
      "units": "MHz",
      "step_coarse": "1",
      "step_fine": "0.001",
      "precision": "0.001"
    },
    "value": {
      "default_value": "0"
    },
    "fader_config": {
      "type": "_GuiFaderHorizontal",
      "cosmetics": {
        "scale": {
          "interval": 100,
          "show": true
        }
      },
      "bar_color": "#333333",
      "active_color": "#FF9900"
    },
    "dial_config": {
      "type": "_GuiKnob",
      "cosmetics": {
        "style_overrides": {
          "knob_style": "dial"
        },
        "colors": {
          "active": "#00ffff",
          "background": "#2b2b2b"
        }
      }
    },
    "value_config": {
      "height": 30,
      "colour": "#ffffff",
      "bg_color": "#1a1a1a",
      "width": 12,
      "font": 18
    },
    "cosmetics": {
      "colors": {
        "primary": "#FF9900",
        "secondary": "#444444",
        "background": "#2b2b2b"
      }
    },
    "_README": "Converted from the deprecated _CompositeFader to the canonical _Horizontal_with_dial_Value: a horizontal fader (whole number) + dial (decimal) that combine into one value."
  }
}
```
