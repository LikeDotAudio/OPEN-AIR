# TextElements — label + value box

Text display primitives: a feature-rich label and a value readout box. The label
mirrors Python's `BuilderTextLabelCreator`.

- **Defines (globals):** `OcaTextLabel`, `OcaTextValueBox`
- **Props:** `value`, `config`
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
  "text_label_from_config_Example": {
    "type": "_SmartLabel",
    "label": "Status",
    "notes": "A basic status indicator.",
    "geometry": {
      "sticky": "ew",
      "font": 18,
      "colour": "#c75450"
    },
    "domain": {
      "primary": {
        "value_default": "Idle"
      }
    },
    "interaction": {
      "is_read_only": false
    },
    "layout": {},
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
