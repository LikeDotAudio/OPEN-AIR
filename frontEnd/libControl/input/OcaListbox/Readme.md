# OcaListbox — listbox (MQTT)

Dynamic single-select list with MQTT synchronization, the web port of Python's
`BuilderListboxCreator`. Accepts array- or object-based option dictionaries.

- **Defines (global):** `OcaListbox`
- **Props:** `value`, `onChange`, `config` (`options`), `topic`, `nodeJson`
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
  "listbox_Example": {
    "type": "_SmartList",
    "label": "Select File",
    "notes": "Listbox for selecting a file from a list.",
    "interaction": {
      "options": {
        "file1": {
          "label": {
            "active": {
              "text": "document.pdf",
              "text_size": 12,
              "text_color": "#cccccc"
            }
          },
          "value": "/path/to/document.pdf",
          "active": "true"
        },
        "file2": {
          "label": {
            "active": {
              "text": "report.docx",
              "text_size": 12,
              "text_color": "#cccccc"
            }
          },
          "value": "/path/to/report.docx",
          "active": "true"
        },
        "file3": {
          "label": {
            "active": {
              "text": "image.png",
              "text_size": 12,
              "text_color": "#cccccc"
            }
          },
          "value": "/path/to/image.png",
          "active": "true",
          "selected": true
        }
      }
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
