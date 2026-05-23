# VUMeterKnob — needle meter + knob

Composite: a `NeedleMeter` with a `Knob` mounted at its pivot (read level, set a
value at the same spot).

- **Defines (global):** `VUMeterKnob`
- **Props:** `value`, `onChange`, `config`, `topic`, `path_prefix`
- **Depends on:** the `NeedleMeter` and `Knob` globals being loaded first.
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
  "meter_knob_with_vu_meter_Example": {
    "widget_type": "_VUMeterKnob",
    "label_active": "Master L",
    "path": "audio/master/left/vu",
    "knob_path": "audio/master/left/gain",
    "size": 200,
    "min": -60,
    "max": 6,
    "knob_min": 0,
    "knob_max": 100,
    "knob_width": 100,
    "knob_height": 100,
    "knob_shape": "circle",
    "knob_pointer_style": "line",
    "knob_outline_thickness": 5,
    "type": "_Meter_Knob_With_Vu_Meter",
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
