# AnimationDisplay (`window.AnimationDisplay`)

Web mirror of `oaGuiElements/Core/images/images_animation_display` — type **`AnimationDisplay`**.

Renders an animated image. The library config carries `gif_path`; the gif is served
through the existing `/api/image?path=…` endpoint (which sets `Content-Type: image/gif`)
and animates natively in an `<img>`. `value` overrides `gif_path` when a live path
arrives over MQTT.

**Config read:** `gif_path` (or `value_default`), `label_active`, `layout`/`geometry`
width/height.

Routed in `frameLayout/WidgetFactory.jsx` (`type === 'AnimationDisplay'` / includes `animation`).

## Sample (WYSIWYG library source)

The web server (`LauchWebserver.py` → `get_grab_bag()`) extracts this block to build
the palette entry, preview, and property manipulators.

```json
{
  "Animation_Display_Example": {
    "type": "AnimationDisplay",
    "label": {
      "active": {
        "text": "Animated Time Circuits",
        "text_size": 12,
        "text_color": "#cccccc"
      }
    },
    "gif_path": "oaDataCache/assets/images/time_circuits.gif",
    "value": {
      "default_value": 0
    },
    "notes": "A standard animation rendered through /api/image.",
    "layout": {
      "sticky": "ew",
      "padx": 5,
      "pady": 5,
      "width": 200,
      "height": 120
    },
    "cosmetics": {
      "colors": {
        "primary": "#FF9900",
        "secondary": "#444444",
        "background": "#2b2b2b"
      }
    }
  },
  "_README": "Animated image widget. gif_path (or value) is served via /api/image and animates natively."
}
```
