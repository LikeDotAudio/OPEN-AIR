# Button — basic actuator + toggle

The simplest button pair: a momentary actuator and a stateful toggle.

- **Defines (globals):** `OcaButton`, `OcaToggleButton`
- **Props:** `OcaButton` → `label`, `onClick`, `color`; `OcaToggleButton` → `label`, `value`, `onChange`
- **Loaded by:** the live app via `frontEnd/Core/Launch/index.html`.
- **Demo:** open `../index.html` (renders both side by side).

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
  "Exhaustive_Actuator_Example": {
    "type": "_GuiActuator",
    "identity": {
      "label": "Fire Pulse",
      "id": "fire_btn",
      "notes": "A momentary push button that triggers a hardware action."
    },
    "geometry": {
      "width": 100,
      "height": 50,
      "corner_radius": 12,
      "stretch": "none"
    },
    "domain": {
      "primary": {
        "value": "TRG:IMM"
      }
    },
    "dynamics": {
      "path": "Hardware/Trigger/Manual"
    },
    "cosmetics": {
      "active_color": "#FF9900",
      "active_bg_color": "#331100",
      "bg_color": "#1a1a1a",
      "active_text_color": "#FFFFFF",
      "text_color": "#dcdcdc",
      "glow_intensity": 1.8,
      "alpha": 1.0,
      "active_font_style": "bold",
      "active_font_size": 12,
      "inactive_font_style": "normal",
      "inactive_font_size": 10
    },
    "readout": {
      "label_active": "FIRING...",
      "label_inactive": "FIRE"
    },
    "interaction": {
      "is_read_only": false,
      "message": "TRG:IMM"
    },
    "layout": {
      "sticky": "center",
      "padx": 10,
      "pady": 10
    }
  },
  "_README": "This sample is REALLY REALLY COMPLETE. It outlines the momentary press behavior and MQTT trigger paths.",
  "_LEGEND": {
    "actuator_types": [
      "_GuiActuator",
      "_SmartActuator",
      "_ButtonActuator",
      "_GuiButton"
    ],
    "momentary_behavior": "Publishes 'val: true' on Press and 'val: false' on Release.",
    "maintenance_commands": "If 'message' starts with '*' (SCPI) or contains 'SYSTem', the command is copied to clipboard instead of published."
  }
}
```
