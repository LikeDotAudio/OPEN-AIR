# OcaSliderValue — slider + entry (MQTT)

Composite slider paired with a text entry box, the web port of Python's
`BuilderSliderValueCreator`.

- **Defines (global):** `OcaSliderValue`
- **Props:** `value`, `onChange`, `config`, `topic`, `nodeJson`
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
  "slider_value_Example": {
    "type": "_sliderValue",
    "label": {
      "active": {
        "text": "Volume",
        "text_size": 12,
        "text_color": "#cccccc"
      },
      "show_label": true
    },
    "layout": {
      "height": 100,
      "width": 250,
      "font": 18
    },
    "domain": {
      "locked": false,
      "min": 0.0,
      "max": 100.0,
      "units": "%"
    },
    "notes": "A standard horizontal slider with numerical input for volume control.",
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
