# TrapezoidButton — 3D trapezoidal button

High-fidelity 3D trapezoid button with state-dependent lighting. Mirrors the
industrial reference at `oaGuiElements/Core/buttons/button_trapezoid`.

- **Defines (global):** `OcaTrapezoidButton`
- **Props:** `label`, `value`, `onChange`, `config` (geometry + cosmetics)
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
  "button_trapezoid_Example": {
    "type": "_TrapezoidButton",
    "label": {
      "active": "Play"
    },
    "min": 0.0,
    "max": 1.0,
    "value_default": false,
    "width": 80,
    "height": 50,
    "color": "#6a9955",
    "led_color": "#00FF00",
    "latching": false,
    "slant": 15,
    "value_text_inside": true,
    "show_value": true,
    "show_units": false,
    "notes": "Momentary, standard green.",
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
