# OcaTextInput — text field (MQTT)

MQTT-synchronized text input with optional units, the web port of Python's
`BuilderTextValueWithUnitsCreator`.

- **Defines (global):** `OcaTextInput`
- **Props:** `value`, `onChange`, `config` (`value_default`, units), `topic`, `nodeJson`
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
  "text_value_with_units_Example": {
    "type": "_SmartInput",
    "label": "Username",
    "notes": "Standard input field for a username.",
    "geometry": {
      "sticky": "ew",
      "font": 16,
      "colour": "#6a9955"
    },
    "domain": {
      "primary": {
        "value_default": "user123"
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
