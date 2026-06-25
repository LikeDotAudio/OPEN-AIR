# NeedleMeter — analog needle (VU) meter

Analog VU-style needle meter with ballistics, tilt, color-zone limits, the full
set of procedural bezel "window" shapes (ported from the Rust needle geometry),
and WASM-generated vintage faces.

- **Defines (globals):** `NeedleMeter`
- **Props:** `value`, `config`
- **Designer:** bespoke `Designer.jsx` (bezel shape, face style, limits, tilt…)
- **Loaded by:** the live app via `frontEnd/Core/Launch/index.html`.

## Config it reads
- `cosmetics.style_overrides.bezel_shape` — gem · super_gem · octagon · triangle ·
  pyramid · hex · hotdog · cylinder · squircle · squimonde · squectangle ·
  trapezoid · badge · crest/shield · parking_meter · stereo_diamond ·
  intersecting_overlay · default. Frame = `cosmetics.colors.bezel` + `bezel_width`.
- `cosmetics.style_overrides.face_style` — none · cream · new_old_stock ·
  vintage_aged · bakelite · tungsten · wood (WASM panel textures + glass sheen).
- `cosmetics.style_overrides.Meter_center_angle` / `Meter_viewable_angle` /
  `Counter_Clockwise` — tilt + direction.
- Limits: `cosmetics.colors.lower|middle|upper` with `cosmetics.scale.mid_range_start`
  + `cosmetics.scale.upper_range` (green → yellow → red).
- `sub_ticks`, `Scale_numbers`, `Pivot_size`, `curve_thickness`, `enable_lighting`.

<!-- wysiwyg:sample (library source — drives the palette entry, preview & editor) -->
## Sample (WYSIWYG library source)

```json
{
  "NeedleMeter": {
    "type": "_NeedleVUMeter",
    "label": { "active": "Master VU", "show_label": true },
    "geometry": { "width": 240, "height": 200 },
    "domain": {
      "primary": { "min": -20, "max": 3, "value_default": -5, "unit": "VU" }
    },
    "dynamics": { "attack_ms": 200, "release_ms": 500 },
    "cosmetics": {
      "colors": {
        "primary": "#33aa33",
        "lower": "#33aa33",
        "middle": "#cccc33",
        "upper": "#cc3333",
        "alert": "#cc3333",
        "pointer": "#ffffff",
        "pivot": "#111111",
        "bezel": "#c0c0c0",
        "faceplate": "#111111",
        "background": "transparent"
      },
      "scale": { "upper_range": 0, "mid_range_start": -6 },
      "style_overrides": {
        "bezel_shape": "default",
        "bezel_width": 8,
        "face_style": "none",
        "enable_lighting": true,
        "Meter_center_angle": 90,
        "Meter_viewable_angle": 90,
        "Counter_Clockwise": false,
        "sub_ticks": 5,
        "Scale_numbers": true,
        "Pivot_size": 10,
        "curve_thickness": 3,
        "show_rule": true,
        "rule_radius_offset": 0,
        "Pointer_Style": "line",
        "needle_size": "medium",
        "Needle_thickness": 2,
        "pivot_offset_x": 0,
        "pivot_offset_y": 0,
        "meter_scale": 1.0,
        "arc_radius_offset": 0,
        "pivot_crop": 0,
        "needle_length_factor": 0.95,
        "tick_length": 8,
        "sub_tick_length": 4,
        "tick_radius_offset": 0,
        "label_radius_offset": 20
      }
    }
  },
  "_LEGEND": {
    "bezel_shape": ["default", "gem", "super_gem", "octagon", "triangle", "pyramid", "hex", "hotdog", "cylinder", "squircle", "squimonde", "squectangle", "trapezoid", "badge", "crest", "shield", "parking_meter", "stereo_diamond", "intersecting_overlay"],
    "face_style": ["none", "cream", "new_old_stock", "vintage_aged", "bakelite", "tungsten", "wood"],
    "needle_size": ["thin", "small", "medium", "large", "xlarge"],
    "Pointer_Style": ["line", "spade", "knife", "baton", "diamond"]
  }
}
```
