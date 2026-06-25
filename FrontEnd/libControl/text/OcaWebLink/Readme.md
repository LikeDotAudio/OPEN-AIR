# OcaWebLink — hyperlink

Simple labelled hyperlink element.

- **Defines (global):** `OcaWebLink`
- **Props:** `config` (`url`, `label`)
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
  "text_web_link_Example": {
    "type": "_SmartLink",
    "label": "Visit Project Homepage",
    "notes": "Link to the main project website.",
    "geometry": {
      "sticky": "ew",
      "font": 14,
      "colour": "#007acc"
    },
    "interaction": {
      "url": "https://www.like.audio/project"
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
