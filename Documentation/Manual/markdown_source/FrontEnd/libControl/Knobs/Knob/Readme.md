# Knob — rotary knob

Rotary control built with separated concerns: motion/angle logic, tick scale,
and the 3D cap body.

- **Defines (globals):** `Knob` (orchestrator), `KnobCap`, `KnobTicks`,
  `getKnobAngles`, `describeArc`, `polarToCartesian`, `shadeHex`
- **Props:** `value`, `onChange`, `config` (domain + cosmetics)
- **Loaded by:** the live app via `frontEnd/Core/Launch/index.html`.
- **Demo:** open `../index.html`.

## Interactions (all visualizations)

- **Drag up/down** → adjust value (clamped, or wrapped if `interaction.infinity`).
- **Mouse wheel** → step by `domain.primary.step` (or 2% of range). Non-passive,
  so it doesn't steal scroll from a containing panel.
- **Alt-click** → snap to `domain.primary.value_default`.

## Visualizations (`cosmetics.visualization`)

`circle` · `octagon` · `gear` (with `styling.teeth`) · `dial` (full 360° sweep) ·
`panner` (centred sweep; outputs `[leftPct, rightPct]` as a 2-element array) ·
`chicken` (round hub + tapered beak + short blunt bum tail) ·
`marconi` (cylinder body + rectangular wing through the body, white indicator
line on the pointer side only) ·
`fender` (INVERTED rotation: face spins under a FIXED pointer; pointer side
configured via `cosmetics.pointer.position`) ·
`api` (4-lobed rounded-square shell with a bright LED-style centre disc and a
corner pointer-notch that protrudes at the value angle; outer shell defaults to
dark unless `styling.fill_color` overrides) ·
`1176` (UA-1176 compressor knob: fluted body + polished metallic top cap, with
**optional flange skirt** (white indicator line on it) and **optional
chicken-foot pointer tab** — all variants config-driven via `cosmetics.flange.{show,color,size}`,
`cosmetics.foot.{show,color,length}`, `cosmetics.styling.cap_color`) ·
`pedal` (guitar-pedal style knob: round colored body + bold white indicator
line + two small side ears at ±90° from the pointer; configurable via
`cosmetics.line.{color,width}`, `cosmetics.ears.{show,size}`) ·
`british` (classic UK / OmterElec fluted cylinder with three optional
variants: **knob** (plain fluted body), **knob with cap** (`cosmetics.cap.show`
— polished metal disc on top), **knob with ring** (`cosmetics.ring.show` —
knurled chrome base ring), **knob with window** (`cosmetics.window.{show,pos,color}`
— small FIXED tick marker on the ring). Number of flutes via `cosmetics.flutes`) ·
`moog` (Minimoog/Voyager-style: polished metal cap with **concentric ring
grooves** (lathe-turned finish — `cosmetics.cap.{show,color,rings}`) on a
cylindrical body that is **fluted** by default (`cosmetics.flutes.{show,count}`)
or smooth. Optional flange (`cosmetics.flange.{show,color,size}`), optional
chicken-foot pointer tab (`cosmetics.foot.{show,color}`), indicator is a
classic Moog DOT on the body edge by default or a LINE
(`cosmetics.indicator.{style,color}`)).

<!-- wysiwyg:sample (auto-generated from oaGuiElements; edit here to drive the library) -->
## Sample (WYSIWYG library source)

The WYSIWYG editor builds this widget's **palette entry, live preview, and
property manipulators** from the JSON block below. The web server
(`frontEnd/Entry.py` → `get_grab_bag()`) scans these READMEs, extracts this
block, and serves it at `/api/grabbag`. `_README` documents the widget; every
`_LEGEND` array becomes a dropdown of allowed values in the property editor.

Every key below is actually read by `Knob.jsx`. Keys that only apply to a
specific visualization are tagged in comments.

```json
{
  "Exhaustive_Knob_Example": {
    "type": "_SmartKnob",
    "label": {
      "En": "Master Tuning",
      "show_label": true
    },
    "geometry": {
      "width": 160,
      "height": 160
    },
    "domain": {
      "primary": {
        "min": 0,
        "max": 100,
        "value_default": 50,
        "step": 1
      }
    },
    "cosmetics": {
      "visualization": "circle",
      "colors": {
        "primary": "#33A1FD",
        "secondary": "#444444",
        "active": "#33A1FD",
        "tick": "#aaaaaa",
        "text": "#caa44a"
      },
      "pointer": {
        "style": "line",
        "length": null,
        "offset": 0,
        "position": "top"
      },
      "scale": {
        "show": true,
        "style": "simple",
        "length": 10,
        "count": 10,
        "thickness": 1,
        "sweep": 300,
        "text_size": null
      },
      "styling": {
        "fill_color": "#333333",
        "outline_color": "#444444",
        "outline_thickness": 0,
        "arc_width": 5,
        "cap_scale": 0.7,
        "no_center": false,
        "teeth": 8
      },
      "style_overrides": {
        "shape": "circle"
      }
    },
    "interaction": {
      "infinity": false
    },
    "layout": {
      "weight": 1,
      "padx": 5,
      "pady": 5
    }
  },
  "_README": "Every key here is actually read by Knob.jsx. cosmetics.visualization picks the cap renderer (circle/octagon/gear/dial/panner/chicken/marconi/fender). chicken+marconi use a beak/wing cap (the beak/wing IS the indicator). fender is the inverted Strat: the FACE rotates (numbers + ribbed skirt) under a FIXED pointer whose side is set by pointer.position. scale.count/sweep/text_size only apply to fender. pointer.position only applies to fender. interaction.infinity true = endless dial (wheel/drag wrap modulo (max-min)). Alt-click any knob snaps to value_default. Panner outputs are an array [leftPct, rightPct]; mid position = [50, 50]. style_overrides.shape can force a cap shape (circle|octagon|gear) independent of visualization. styling.teeth only applies when the cap is rendered as a gear.",
  "_LEGEND": {
    "visualization_types": [
      "circle",
      "octagon",
      "gear",
      "dial",
      "panner",
      "chicken",
      "marconi",
      "fender",
      "api",
      "1176",
      "pedal",
      "british",
      "moog"
    ],
    "pointer_styles": [
      "line",
      "triangle",
      "dot",
      "notch",
      "thin",
      "block",
      "tapered",
      "vintage"
    ],
    "pointer_positions": [
      "top",
      "bottom",
      "left",
      "right"
    ],
    "tick_styles": [
      "simple",
      "dots",
      "numeric"
    ],
    "shapes": [
      "circle",
      "octagon",
      "gear"
    ]
  },
  "Crafty_Spoked": {
    "type": "_SmartKnob",
    "label": {
      "En": "Delay",
      "show_label": true
    },
    "geometry": {
      "width": 80,
      "height": 80
    },
    "cosmetics": {
      "visualization": "crafty",
      "variant": "spoked",
      "colors": {
        "primary": "#ffffff",
        "secondary": "#5a3d7c"
      }
    }
  },
  "Crafty_Metallic": {
    "type": "_SmartKnob",
    "label": {
      "En": "Phase",
      "show_label": true
    },
    "geometry": {
      "width": 80,
      "height": 80
    },
    "cosmetics": {
      "visualization": "crafty",
      "variant": "metallic",
      "colors": {
        "primary": "#222222",
        "secondary": "#444444"
      }
    }
  },
  "Crafty_LED_Ring": {
    "type": "_SmartKnob",
    "label": {
      "En": "Mic",
      "show_label": true
    },
    "geometry": {
      "width": 80,
      "height": 80
    },
    "cosmetics": {
      "visualization": "crafty",
      "variant": "led_ring",
      "colors": {
        "primary": "#88e077",
        "secondary": "#444444"
      }
    }
  }
}
```
