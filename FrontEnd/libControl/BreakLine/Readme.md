# BreakLine — divider rule

A thin horizontal or vertical separator line for laying out panels.

- **Defines (global):** `BreakLine` (also `window.BreakLine`)
- **Props:** `config` — `{ orientation: 'horizontal'|'vertical', color, thickness, margin }`
- **Loaded by:** the live app via `frontEnd/Core/Launch/index.html`.

Pure presentation; no MQTT, no state.

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
  "break_line_Example": {
    "type": "OcaBreakLine",
    "layout": {
      "height": 2,
      "padx": 10,
      "pady": 5,
      "colour": "#555555",
      "alpha": 1.0,
      "sticky": "ew"
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
