# InputElements — basic input bundle

A small bundle of plain form controls used by the input demo.

- **Defines (globals):** `OcaCheckbox`, `OcaDropdown`, `OcaIncDecButtons`
- **Loaded by:** the live app via `frontEnd/Core/Launch/index.html`.
- **Demo:** open `../index.html`.

> **Note:** `OcaCheckbox` here is the simple form variant. The MQTT-aware
> `OcaCheckbox` lives in `../OcaCheckbox/` and is loaded **after** this file in
> `Core/Launch/index.html`, so it wins (same global name). Keep that load order
> in mind if you edit either.

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
  "text_gui_dropdown_option_Example": {
    "type": "_GuiDropDownOption",
    "label": "Input",
    "options": {
      "Mic1": {
        "label": {
          "active": "Microphone 1"
        },
        "value": "MIC1_IN",
        "selected": true
      },
      "Mic2": {
        "label": {
          "active": "Microphone 2"
        },
        "value": "MIC2_IN"
      },
      "LineIn": {
        "label": {
          "active": "Line Input"
        },
        "value": "LINE_IN"
      }
    },
    "notes": "Dropdown for selecting an audio input source.",
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
