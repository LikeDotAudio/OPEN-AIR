# Radar (`window.Radar`)

Web mirror of `oaGuiElements/Core/graphing/radar` — type **`_Radar`**.

A radial "radar scope": pure-SVG polar grid (rings every `grid_system.ring_interval`,
spokes every `grid_system.spoke_interval`) with a value sweep around one revolution.

**Config read:** `data_parameters {min_value, max_value, points_per_revolution,
start_angle, clockwise}`, `visuals.plot_style` (`area` | `line`),
`grid_system {show_grid, grid_color, ring_interval, spoke_interval, labels.show_values}`,
`color_thresholds.colors.safe` (sweep color), `cosmetics.colors.background`.

**Data:** `value` may be an array of numbers (mapped evenly around 360°) or an array
of `[angleDeg, value]` pairs. With no data it draws a faint demo lobe.

Routed in `frameLayout/WidgetFactory.jsx` (`type === '_Radar'` / includes `radar`).

## Sample (WYSIWYG library source)

The web server (`LauchWebserver.py` → `get_grab_bag()`) extracts this block to build
the palette entry, preview, and property manipulators.

```json
{
  "Radar_Scope_Example": {
    "type": "_Radar",
    "label": {
      "active": {
        "text": "Radar Eye 01",
        "text_size": 12,
        "text_color": "#cccccc"
      }
    },
    "data_parameters": {
      "min_value": 0,
      "max_value": 100,
      "points_per_revolution": 360,
      "start_angle": 90,
      "clockwise": true
    },
    "visuals": {
      "plot_style": "area"
    },
    "grid_system": {
      "show_grid": true,
      "grid_color": "#86c0db",
      "ring_interval": 20,
      "spoke_interval": 30,
      "labels": {
        "show_values": true
      }
    },
    "color_thresholds": {
      "colors": {
        "safe": "#0c75ec",
        "warning": "#2f6988",
        "critical": "#455594"
      }
    },
    "layout": {
      "sticky": "ew",
      "padx": 5,
      "pady": 5,
      "width": 240,
      "height": 240
    },
    "cosmetics": {
      "colors": {
        "primary": "#FF9900",
        "secondary": "#444444",
        "background": "#0a0f12"
      }
    }
  },
  "_README": "Radial radar scope: polar rings/spokes with a value sweep around one revolution.",
  "_LEGEND": {
    "plot_style": [
      "area",
      "line"
    ]
  }
}
```
