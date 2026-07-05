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
  "Exhaustive_GCA_Example": {
    "type": "_GCA",
    "label": {
      "active": {
        "text": {
          "En": "RGB Mixer",
          "Fr": "Mélangeur RGB",
          "De": "RGB-Mischer",
          "Es": "Mezclador RGB"
        },
        "text_size": 12,
        "text_color": "#cccccc"
      }
    },
    "layout": {
      "width": 140,
      "height": 380,
      "alpha": 0.9
    },
    "domain": {
      "min": 0,
      "max": 100
    },
    "is_rgb": true,
    "num_channels": 3,
    "active_color": "#f4902c",
    "sub_label": "COLOR",
    "channels": [
      { "default": 10, "label": { "En": "R" } },
      { "default": 50, "label": { "En": "G" } },
      { "default": 20, "label": { "En": "B" } }
    ],
    "value": {
      "default_value": 0
    },
    "cosmetics": {
      "colors": {
        "background": "#2b2b2b"
      }
    },
    "_README": "A complete GCA component example showing RGB mode and channel overrides."
  }
}
```
