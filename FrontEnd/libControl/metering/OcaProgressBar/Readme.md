# OcaProgressBar — progress bar

Minimal normalized progress/fill bar.

- **Defines (global):** `OcaProgressBar`
- **Props:** `value`, `config` (`min`, `max`, `cosmetics.colors.primary`)
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
  "images_progress_bar_Example": {
    "type": "_SmartProgress",
    "label": "Progress",
    "notes": "Shows the progress of a download.",
    "domain": {
      "primary": {
        "max": 100,
        "value_default": 25
      }
    },
    "interaction": {
      "is_read_only": false
    },
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
