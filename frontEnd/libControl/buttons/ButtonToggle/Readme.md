# ButtonToggle — stateful toggle (MQTT)

Stateful ON/OFF toggle button, the web port of Python's `ToggleButton`.

- **Defines (global):** `ButtonToggle`
- **Props:** `value`, `onChange`, `config`, `topic`, `nodeJson`
- **MQTT:** when `topic` is set, state is bound through `window.useMqttState`; otherwise it falls back to `value`/`onChange`. Labels are localized via `window.useMqttLang`.
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
  "Exhaustive_Toggle_Example": {
    "type": "_SmartToggle",
    "identity": {
      "label": "Mute Control",
      "id": "mute_btn",
      "notes": "A boolean toggle button with custom photorealistic states."
    },
    "geometry": {
      "width": 120,
      "height": 50,
      "corner_radius": 8,
      "stretch": "none"
    },
    "domain": {
      "primary": {
        "value_default": false
      }
    },
    "dynamics": {
      "path": "Audio/Output/Mute"
    },
    "cosmetics": {
      "alpha": 1.0
    },
    "style": {
      "active": {
        "font_style": "bold",
        "font_size": 11,
        "text_color": "#FFFFFF",
        "bg_color": "#220000",
        "border_color": "#FF3300",
        "border_thickness": 2,
        "glow_intensity": 1.5
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
    "readout": {
      "label_position": "top"
    },
    "interaction": {
      "is_read_only": false,
      "options": {
        "ON": {
          "label": {
            "active": "MUTED"
          },
          "selected": false
        },
        "OFF": {
          "label": {
            "inactive": "LIVE"
          },
          "selected": true
        }
      }
    },
    "layout": {
      "sticky": "nw",
      "padx": 10,
      "pady": 10
    }
  },
  "_README": "This sample is REALLY REALLY COMPLETE. It follows the 5-pillar 'Universal Rhyme' schema and outlines the state-specific labels used for boolean logic.",
  "_LEGEND": {
    "toggle_types": [
      "_SmartToggle",
      "_GuiButtonToggle"
    ],
    "options_keys": "The 'ON' and 'OFF' keys in interaction.options are mandatory for boolean mapping.",
    "font_styles": [
      "normal",
      "bold",
      "italic"
    ],
    "style_states": [
      "active",
      "inactive"
    ],
    "style_params": "style.active and style.inactive carry the SAME params: font_style, font_size, text_color, bg_color, border_color, border_thickness, glow_intensity."
  }
}
```
