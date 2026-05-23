# LTPFader — Linear Travelling Potentiometer

Dual-axis controller: linear travel plus rotation, on a canvas. Hold the
modifier to engage the rotation axis.

- **Defines (global):** `LTPFader`
- **Props:** `config`, `value`, `rotValue`, `onChange`
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
  "fader_linear_travelling_potentiometer_Example": {
    "type": "_CustomLTP",
    "label": {
      "active": "Master Gali"
    },
    "notes": "A fully-featured Linear Travelling Potentiometer (LTP) sample showcasing every parameter.",
    "fader_config": {
      "value_min": -100.0,
      "value_max": 20.0,
      "value_default": -10.0,
      "log_exponent": 1.0,
      "reff_point": 0.0,
      "value_highlight_color": "#33A1FD",
      "show_value": true,
      "show_units": true,
      "unit_text": "dB",
      "unit_position": "right"
    },
    "knob_config": {
      "rotation_min": -100.0,
      "rotation_max": 100.0,
      "rotation_default": 0.0,
      "cap_radius": 22,
      "cap_color": "#1a1a1a",
      "cap_outline_color": "#FF6B35",
      "freestyle": true,
      "knob_style": "standard",
      "gradient_level": 2
    },
    "style": {
      "knob_shape": "octagon",
      "knob_teeth": 12,
      "pointer_style": "line",
      "arc_width": 3,
      "tick_color": "#666666",
      "sub_tick_color": "#444444",
      "tick_font_size": 9,
      "tick_label_position": "right",
      "value_color": "#33A1FD",
      "value_follow": true,
      "label_color": "#ffffff",
      "border_width": 0,
      "border_color": "#000000"
    },
    "layout": {
      "width": 100,
      "height": 450,
      "padx": 10,
      "pady": 10,
      "font": 12,
      "colour": "#dcdcdc"
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
