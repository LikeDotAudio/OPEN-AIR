# MDP — Multi-Dimensional Panner

Advanced multi-axis panner (X, Y, linear, rotation) with widget rotation and
free move, on a canvas. Robust numeric extraction for MQTT composite states.
Mirrors `oaGuiElements/Core/special/composite_mdp`.

- **Defines (global):** `MDP`
- **Props:** `config`, `value`, `rotValue`, `angle`, `onChange`
- **Loaded by:** the live app via `frontEnd/Core/Launch/index.html` (this is the
  wired-in panner; the `faders/MDP` copy is not loaded).

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
  "composite_mdp_Example": {
    "type": "_MDP",
    "label": {
      "active": "MDP 1"
    },
    "path": "audio/mdp/1",
    "initial_x": 210,
    "initial_y": 125,
    "graph": {
      "title": "XY Space",
      "show_title": false,
      "show_grid": true,
      "show_legend": false,
      "show_axis": true,
      "xlim": [
        0,
        20
      ],
      "ylim": [
        0,
        20
      ],
      "style": {
        "bg_color": "#000000",
        "grid_color": "#666666",
        "title_color": "white",
        "axis_color": "white"
      },
      "axis": {
        "x": {
          "label": "X",
          "color": "white",
          "scale": "linear"
        },
        "y": {
          "label": "Y",
          "color": "white",
          "scale": "linear"
        }
      },
      "datasets": [
        {
          "id": "grid_ref",
          "label": "Grid Ref",
          "style": {
            "line_color": "cyan"
          },
          "initial_csv_data": "x,y\n0,0\n20,20"
        }
      ]
    },
    "ltp": {
      "label": {
        "active": "Level"
      },
      "value_default": -10,
      "cap_color": "#00FF00",
      "freestyle": true,
      "knob_style": "standard"
    },
    "layout": {
      "width": 500,
      "height": 500
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
