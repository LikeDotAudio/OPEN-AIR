# DualFader — two-handle fader

Single track carrying two independent handles (e.g. min/max or L/R).

- **Defines (globals):** `DualFader`, `clamp`
- **Props:** `value`, `onChange`, `config` (`domain.primary.min/max`, `geometry.width/height`)
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
  "fader_dual_Example": {
    "type": "_CustomDualHorizontalFader",
    "label": "Horizontal Dual Fader",
    "notes": "Standard horizontal configuration",
    "geometry": {
      "width": 400,
      "height": 100,
      "font": 12,
      "colour": "#FFFFFF",
      "orientation": "horizontal"
    },
    "domain": {
      "primary": {
        "min": -100.0,
        "max": 20.0,
        "value_default_v1": -10.0,
        "value_default_v2": -20.0,
        "law": "linear",
        "log_exponent": 1.0
      }
    },
    "cosmetics": {
      "colors": {
        "primary": "#dcdcdc"
      },
      "style_flags": {},
      "style_overrides": {
        "cap_width": 40,
        "cap_height_ratio": 0.5,
        "cap_radius": 5,
        "value_follow": true,
        "border_width": 1,
        "border_color": "#444444"
      }
    },
    "interaction": {
      "is_read_only": false
    },
    "layout": {}
  },
  "_README": "This is an enhanced sample configuration demonstrating full instantiation capabilities."
}
```
