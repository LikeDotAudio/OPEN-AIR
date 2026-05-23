# OcaCheckbox — checkbox (MQTT)

Canvas-styled checkbox with MQTT synchronization, the web port of Python's
`BuilderCheckboxCreator`.

- **Defines (global):** `OcaCheckbox`
- **Props:** `value`, `onChange`, `config`, `topic`, `nodeJson`
- **MQTT:** binds through `window.useMqttState` when `topic` is set.
- **Loaded by:** the live app via `frontEnd/Core/Launch/index.html` (after
  `InputElements`, so this MQTT version is the effective `OcaCheckbox`).

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
  "checkbox_Example": {
    "type": "_SmartCheckbox",
    "label": "Feature Enabled",
    "notes": "Checkbox to enable/disable a specific feature.",
    "domain": {
      "primary": {
        "value_default": false
      }
    },
    "interaction": {
      "is_read_only": false
    },
    "label_inactive": "Feature Disabled",
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
