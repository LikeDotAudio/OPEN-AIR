# WinkButton — animated shutter indicator

Indicator/button with an animated "wink" shutter; round or rounded-rect, sized
from `config.geometry`. Port of Python's `wink_config.py` styling.

- **Defines (global):** `OcaWinkButton`
- **Props:** `label`, `value`, `onChange`, `config` (geometry, `shape_type`, colors)
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
  "button_wink_Example": {
    "type": "_WinkButton",
    "label": {
      "active": "01"
    },
    "path": "audio/wink/target_demo_001",
    "width": 60,
    "height": 60,
    "shape_type": "square",
    "color": "#00FF00",
    "shutter_color": "#000000",
    "latching": false,
    "open_speed": 0.22,
    "close_speed": 0.33,
    "text_inside": "GO",
    "text_inside_color": "white",
    "radius": 0,
    "text_closed": "",
    "layout": {
      "sticky": "ew",
      "padx": 5,
      "pady": 5,
      "width": 100,
      "height": 50
    },
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
