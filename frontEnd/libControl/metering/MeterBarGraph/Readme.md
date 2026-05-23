# MeterBarGraph — bar meter

Bar-graph level meter with smoothing/peak-hold ballistics and a labelled scale.
Separated concerns: ballistics hook, scale, body, orchestrator.

- **Defines (globals):** `MeterBarGraph` (orchestrator), `MeterBody`, `MeterScale`, `useMeterBallistics`
- **Props:** `value`, `config` (min/max, orientation, cosmetics)
- **Loaded by:** the live app via `frontEnd/Core/Launch/index.html`.
- **Demo:** open `../index.html`.

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
  "meter_bar_Example": {
    "type": "DynamicBarGraph",
    "label": "Metric Comparison",
    "notes": "Demonstrates categorical data as bars.",
    "show_title": true,
    "title": "System Resource Usage",
    "layout": {
      "height": 50,
      "alpha": 0.9
    },
    "axis": {
      "x": {
        "label": "Resource ID",
        "color": "white"
      },
      "y": {
        "label": "Usage (%)",
        "min": 0,
        "max": 100,
        "color": "cyan"
      },
      "show_grid": true,
      "show_x_axis": true,
      "show_y_axis": true
    },
    "datasets": [
      {
        "id": "ds_usage",
        "label": "Usage",
        "style": {
          "line_color": "cyan",
          "line_width": 1
        },
        "initial_csv_data": "x,y\n1,45\n2,78\n3,12\n4,90\n5,55"
      }
    ],
    "Navigation": {
      "enable_zoom": true,
      "enable_pan": true,
      "show_hover_value": true
    },
    "initial_markers": "y,80,red,2,Warning Threshold",
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
