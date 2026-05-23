# TrapezoidButtonToggler (`window.TrapezoidButtonToggler`)

Web mirror of `oaGuiElements/Core/buttons/button_trapezoid_toggler` — type
**`_TrapezoidButtonToggler`**.

A radio/multi **group** of trapezoid buttons — reuses `OcaTrapezoidButton` per option
and the same selection semantics as `ButtonToggler`:
- `selection_mode`: `radio` (one at a time, default) | `multi`
- `Allow_Null`: a radio click on the active option clears it
- `options`: array (`["Mic","Line","USB"]`) or dict (`{ "1": {label_active,color} }`)
- per-option `color`/`led_color`; group `slant`, `width`, `height`, `layout.max_cols`

Routed in `frameLayout/WidgetFactory.jsx` (toggler branch: trapezoid + toggler).

## Sample (WYSIWYG library source)

The web server (`LauchWebserver.py` → `get_grab_bag()`) extracts this block to build
the palette entry, preview, and property manipulators.

```json
{
  "Trapezoid_Toggler_Example": {
    "type": "_TrapezoidButtonToggler",
    "label": {
      "active": "Input"
    },
    "options": [
      "Mic",
      "Line",
      "USB"
    ],
    "value_default": "Mic",
    "selection_mode": "radio",
    "Allow_Null": false,
    "width": 80,
    "height": 50,
    "color": "#6a9955",
    "led_color": "#00FF00",
    "slant": 15,
    "layout": {
      "sticky": "ew",
      "padx": 5,
      "pady": 5,
      "max_cols": 3
    },
    "cosmetics": {
      "colors": {
        "primary": "#FF9900",
        "secondary": "#444444",
        "background": "#2b2b2b"
      }
    }
  },
  "_README": "Radio/multi group of trapezoid buttons (reuses OcaTrapezoidButton per option).",
  "_LEGEND": {
    "selection_modes": [
      "radio",
      "multi"
    ]
  }
}
```
