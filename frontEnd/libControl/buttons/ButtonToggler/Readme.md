# ButtonToggler — radio group (MQTT)

Mutually-exclusive button group (radio behaviour), the web port of Python's
`TogglerButton`.

- **Defines (global):** `ButtonToggler`
- **Props:** `value`, `onChange`, `config`, `topic`, `nodeJson`
- **Options:** `config.options` accepts either an array or an object dictionary.
- **MQTT:** binds through `window.useMqttState` when `topic` is set; labels via `window.useMqttLang`.
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
  "Exhaustive_Toggler_Example": {
    "type": "_SmartToggler",
    "identity": {
      "label": "Filter Mode",
      "id": "filter_group",
      "notes": "A multi-state radio group with photorealistic buttons."
    },
    "geometry": {
      "width": 160,
      "height": 50,
      "max_cols": 3,
      "padx": 5,
      "pady": 5,
      "corner_radius": 6,
      "stretch": "width"
    },
    "domain": {
      "primary": {
        "value_default": "LPF"
      }
    },
    "dynamics": {
      "path": "DSP/Filter/Type"
    },
    "cosmetics": {
      "alpha": 0.9
    },
    "style": {
      "active": {
        "font_style": "bold",
        "font_size": 10,
        "text_color": "#1a1a1a",
        "bg_color": "#000000",
        "border_color": "#33A1FD",
        "border_thickness": 2,
        "glow_intensity": 1.2
      },
      "inactive": {
        "font_style": "normal",
        "font_size": 10,
        "text_color": "#888888",
        "bg_color": "#1a1a1a",
        "border_color": "#555555",
        "border_thickness": 2,
        "glow_intensity": 0
      }
    },
    "interaction": {
      "selection_mode": "radio",
      "Allow_Null": false,
      "Allow_Multi_Alt_Select": true,
      "options": {
        "LPF": {
          "label_active": "LOW PASS",
          "label_inactive": "LPF",
          "selected": true,
          "active_color": "#00FF00"
        },
        "HPF": {
          "label_active": "HIGH PASS",
          "label_inactive": "HPF",
          "selected": false
        },
        "BPF": {
          "label_active": "BAND PASS",
          "label_inactive": "BPF",
          "selected": false
        }
      }
    },
    "layout": {
      "sticky": "ew",
      "padx": 10,
      "pady": 10
    }
  },
  "_README": "This sample is REALLY REALLY COMPLETE. It outlines multi-column grid logic, selection modes, and per-option styling overrides.",
  "_LEGEND": {
    "toggler_types": [
      "_SmartToggler",
      "_GuiButtonToggler"
    ],
    "selection_modes": [
      "radio",
      "multi"
    ],
    "Allow_Null": "If true, clicking an active button deselects it (empty state).",
    "Allow_Multi_Alt_Select": "If true, holding ALT allows multi-selection even in radio mode.",
    "option_overrides": "Each option can have its own 'active_color' or 'bg_color'.",
    "font_styles": ["normal", "bold", "italic"],
    "style_states": ["active", "inactive"],
    "style_params": "style.active and style.inactive carry the SAME params: font_style, font_size, text_color, bg_color, border_color, border_thickness, glow_intensity."
  }
}
```
