# HighVisButton — Prominent bordered button (MQTT)

A button component characterized by a thick outer rim/bezel and a dark pushable inner area. Commonly used for prominent UI actions like MUTE, SOLO, ISO, and prominent toggles.

- **Defines (global):** `HighVisButton`
- **Props:** `value`, `onChange`, `config`, `topic`, `nodeJson`
- **MQTT:** Binds state through `window.useMqttState` when a `topic` is provided.

<!-- wysiwyg:sample (auto-generated from oaGuiElements; edit here to drive the library) -->
## Sample (WYSIWYG library source)

```json
{
  "HighVis_MUTE_Example": {
    "type": "_HighVisButton",
    "identity": {
      "label": "Mute Button",
      "id": "mute_btn",
      "notes": "A high-visibility Mute button."
    },
    "geometry": {
      "width": 80,
      "height": 45,
      "corner_radius": 8
    },
    "domain": {
      "primary": {
        "value_default": false
      }
    },
    "cosmetics": {
      "shape": "rect"
    },
    "style": {
      "active": {
        "text_color": "#FF6b35",
        "rim_color": "#4A6EAA",
        "inner_bg_color": "#222222",
        "glow_intensity": 6
      },
      "inactive": {
        "text_color": "#999999",
        "rim_color": "#E0E0E0",
        "inner_bg_color": "#2a2a2a",
        "glow_intensity": 0
      }
    },
    "interaction": {
      "is_read_only": false,
      "options": {
        "ON": {
          "label": {
            "active": {
              "text": "MUTE"
            }
          },
          "selected": false
        },
        "OFF": {
          "label": {
            "inactive": {
              "text": "MUTE"
            }
          },
          "selected": true
        }
      }
    },
    "layout": {
      "sticky": "ew",
      "padx": 5,
      "pady": 5
    }
  },
  "HighVis_SOLO_Example": {
    "type": "_HighVisButton",
    "identity": {
      "label": "Solo Button",
      "id": "solo_btn"
    },
    "geometry": {
      "width": 80,
      "height": 45,
      "corner_radius": 8
    },
    "domain": {
      "primary": {
        "value_default": false
      }
    },
    "cosmetics": {
      "shape": "rect"
    },
    "style": {
      "active": {
        "text_color": "#FFFFFF",
        "rim_color": "#FAD02C",
        "inner_bg_color": "#222222",
        "glow_intensity": 8
      },
      "inactive": {
        "text_color": "#FFFFFF",
        "rim_color": "#E0E0E0",
        "inner_bg_color": "#111111",
        "glow_intensity": 0
      }
    },
    "interaction": {
      "options": {
        "ON": { "label": { "active": { "text": "SOLO" } } },
        "OFF": { "label": { "inactive": { "text": "SOLO" } } }
      }
    },
    "layout": {
      "sticky": "ew",
      "padx": 5,
      "pady": 5
    }
  },
  "HighVis_ISO_Example": {
    "type": "_HighVisButton",
    "identity": {
      "label": "ISO Button",
      "id": "iso_btn"
    },
    "geometry": {
      "width": 60,
      "height": 45,
      "corner_radius": 8
    },
    "domain": {
      "primary": {
        "value_default": false
      }
    },
    "cosmetics": {
      "shape": "rect"
    },
    "style": {
      "active": {
        "text_color": "#FFFFFF",
        "rim_color": "#33CC66",
        "inner_bg_color": "#222222",
        "glow_intensity": 5
      },
      "inactive": {
        "text_color": "#CCCCCC",
        "rim_color": "#E0E0E0",
        "inner_bg_color": "#111111",
        "glow_intensity": 0
      }
    },
    "interaction": {
      "options": {
        "ON": { "label": { "active": { "text": "ISO" } } },
        "OFF": { "label": { "inactive": { "text": "ISO" } } }
      }
    },
    "layout": {
      "sticky": "ew",
      "padx": 5,
      "pady": 5
    }
  },
  "HighVis_Pill_Example": {
    "type": "_HighVisButton",
    "identity": {
      "label": "Pill Button",
      "id": "pill_btn"
    },
    "geometry": {
      "width": 100,
      "height": 40
    },
    "domain": {
      "primary": {
        "value_default": false
      }
    },
    "cosmetics": {
      "shape": "pill"
    },
    "style": {
      "active": {
        "text_color": "#FFFFFF",
        "rim_color": "#FFFFFF",
        "inner_bg_color": "#222222",
        "glow_intensity": 4
      },
      "inactive": {
        "text_color": "#FFFFFF",
        "rim_color": "#AAAAAA",
        "inner_bg_color": "#333333",
        "glow_intensity": 0
      }
    },
    "interaction": {
      "options": {
        "ON": { "label": { "active": { "text": "CHANNEL" } } },
        "OFF": { "label": { "inactive": { "text": "CHANNEL" } } }
      }
    },
    "layout": {
      "sticky": "ew",
      "padx": 5,
      "pady": 5
    }
  },
  "_README": "The HighVisButton provides a strong outer bezel that can change color or glow, with a central dark pill/rect that receives the label text."
}
```
