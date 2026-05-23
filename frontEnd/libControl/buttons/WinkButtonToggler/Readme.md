# WinkButtonToggler (`window.WinkButtonToggler`)

Web mirror of `oaGuiElements/Core/buttons/button_wink_toggler` — type
**`_WinkButtonToggler`**.

A radio/multi **group** of "wink" (shutter) buttons — reuses `OcaWinkButton` per
option; the selected option is held OPEN (lit), the others closed. Selection
semantics match `ButtonToggler`:
- `selection_mode`: `radio` (default) | `multi`; `Allow_Null` lets a radio click clear
- `options`: array or dict with per-option `color`
- group `shape_type`, `radius`, `shutter_color`, `bezel_color`, `open_speed`,
  `close_speed`, `width`, `height`, `layout_columns`

Routed in `frameLayout/WidgetFactory.jsx` (toggler branch: wink + toggler).

## Sample (WYSIWYG library source)

The web server (`LauchWebserver.py` → `get_grab_bag()`) extracts this block to build
the palette entry, preview, and property manipulators.

```json
{
  "Wink_Toggler_Example": {
    "type": "_WinkButtonToggler",
    "label_active": "Channel",
    "layout_columns": 3,
    "options": {
      "1": { "label_active": "1", "color": "#FF0000" },
      "2": { "label_active": "2", "color": "#FF7F00" },
      "3": { "label_active": "3", "color": "#FFFF00" },
      "4": { "label_active": "4", "color": "#00FF00" },
      "5": { "label_active": "5", "color": "#0000FF" },
      "6": { "label_active": "6", "color": "#4B0082" }
    },
    "value_default": "1",
    "selection_mode": "radio",
    "width": 80,
    "height": 30,
    "shape_type": "rect",
    "radius": 5,
    "shutter_color": "black",
    "bezel_color": "#2b2b2b",
    "open_speed": 1200,
    "close_speed": 600,
    "layout": { "sticky": "ew", "padx": 5, "pady": 5 }
  },
  "_README": "Radio/multi group of wink (shutter) buttons; the selected option is held open.",
  "_LEGEND": {
    "selection_modes": ["radio", "multi"],
    "shape_type": ["rect", "round", "rounded_rect"]
  }
}
```
