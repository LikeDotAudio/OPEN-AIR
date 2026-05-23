# JsonTree — collapsible JSON viewer

Recursive, expandable tree view of an arbitrary JSON object.

- **Defines (globals):** `OcaJsonTree`, `JsonNode` (recursive node)
- **Props:** the JSON value to display (per `OcaJsonTree`)
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
  "data_json_tree_Example": {
    "type": "_JsonTree",
    "label_active": "AES70 Object Model (data_AES70.json)",
    "json_source": "display/right_50/bottom_90/10_sets/3_AES70/data_AES70.json",
    "allow_filter": true,
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
