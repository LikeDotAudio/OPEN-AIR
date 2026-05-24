# FaderWithMeter — fader beside a meter

Composite that pairs a fader with an adjacent meter bar (level alongside
control). Builds a sub-config and reuses the fader internals.

- **Defines (global):** `FaderWithMeter`
- **Props:** `value`, `onChange`, `config` (`layout.width/height`, `meter_width`, `fader_width`, `bar_enable`)
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
  "fader_bar_graph_Example": {
    "type": "_FaderWithBarGraph",
    "label": {
      "active": {
        "text": "Standard",
        "text_size": 12,
        "text_color": "#cccccc"
      }
    },
    "domain": {
      "locked": false,
      "min": -60.0,
      "max": 10.0
    },
    "value": {
      "default_value": -10.0
    },
    "layout": {
      "height": 300,
      "width": 120
    },
    "meter_width": 15,
    "cap_height": 40,
    "show_ticks": true,
    "tick_steps": 10,
    "cosmetics": {
      "colors": {
        "primary": "#FF9900",
        "secondary": "#444444",
        "background": "#2b2b2b"
      }
    }
  },
  "_README": "This is an enhanced sample configuration demonstrating full instantiation capabilities."
}
```
