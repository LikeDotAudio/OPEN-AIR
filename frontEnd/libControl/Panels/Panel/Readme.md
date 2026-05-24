# Panel — procedural background "cover" (WASM)

`window.Panel` renders a procedurally generated industrial panel into a `<canvas>`
and blits it behind whatever it wraps. The texture is produced by the Rust→WASM
engine in `../wasm` (`window.OAPanels.generatePanel`) — the same layered pipeline
the Python desktop generator used (substrate → paint → vignette → rust →
scratches → stains → **auto-placed screws** → metal-fold → dust → global blur).

It is **static**: no animation, no MQTT. It only regenerates when its box size or
its config changes, and caches results by `WxH|configJSON`.

## How it is used

**1. Global default** — every `OcaBin` renders the global cover
(`window.OA_PANEL_DEFAULT_CONFIG`, defined in `../panel_wasm_loader.js`) behind
its content automatically.

**2. Page/container declares its own** — set a `background` object on the OcaBin
(the established schema; `cosmetics.panel` / `panel` are also accepted):

```jsonc
{
  "type": "OcaBin",
  "background": {
    "parameters": {
      "base_material": { "color": "#444444", "texture_type": "wrinkle" },
      "dust": { "enabled": true, "intensity": 0.7 }
    }
  }
}
```

Set `"enabled": false` on that object to opt a bin out of any cover.

**3. Explicit widget** — drop a `panel` field anywhere via the layout JSON / the
WYSIWYG palette (sample below).

## Config schema (under `parameters`)

| group | keys |
|-------|------|
| `random_seed` | int — deterministic seed |
| `global_blur` | float — final Gaussian blur |
| `base_material` | `color` (hex), `texture_type` (`flat`/`brushed`/`hammered`/`crosshatch`/`wrinkle`/`enamel`), `grain_direction` |
| `paint_layer` | `color`, `opacity` 0–1, `gradient_intensity` |
| `edge_wear` | `enabled`, `scratch_depth`, `scratch_intensity`, `fade_depth`, `vignette_intensity` |
| `panel_scratches` | `count`, `intensity`, `min_length_px`, `max_length_px`, `width_px`, `depth_highlight`, `reveals_substrate` |
| `rust` | `enabled`, `intensity` |
| `grime` | `stain_count`, `color`, `opacity`, `stain_spread` |
| `screws` | `enabled`, `type` (`fillister`/`countersunk`), `finish` (`chrome`/`black`), `size_px`, `locations` `["top","bottom","middle"]` |
| `metal_fold` | `enabled`, `width_px`, `creases:[{orientation,position_pct}]`, `repeat_screws` |
| `dust` | `enabled`, `intensity` |
| `studio_haze` | `enabled`, `intensity` |

## Grab-bag sample

```json
{
  "Panel": {
    "type": "panel",
    "geometry": { "width": 320, "height": 200 },
    "panel": {
      "parameters": {
        "random_seed": 7,
        "global_blur": 0.5,
        "base_material": { "color": "#2a2a2a", "texture_type": "brushed", "grain_intensity": 0.35 },
        "paint_layer": { "color": "#3a4a5a", "opacity": 0.12, "gradient_intensity": 0.2 },
        "edge_wear": { "enabled": true, "fade_depth": 30, "vignette_intensity": 0.5 },
        "screws": { "enabled": true, "type": "fillister", "finish": "chrome", "size_px": 20, "locations": ["top", "bottom"] }
      }
    }
  }
}
```

## Rebuilding the WASM

```bash
cd frontEnd/libControl/Panels/wasm
wasm-pack build --target no-modules --release --out-dir pkg
```

Outputs `pkg/oa_panels.js` + `pkg/oa_panels_bg.wasm`, served directly by the
Python web server (no bundler step).
