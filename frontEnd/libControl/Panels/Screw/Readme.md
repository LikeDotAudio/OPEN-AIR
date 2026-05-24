# Screw — procedural Robertson screw (WASM)

`window.Screw` renders a single procedural Robertson screw head into a `<canvas>`
via the WASM engine (`window.OAPanels.generateScrew`). It is the standalone
counterpart to the screws the `Panel` cover auto-places at its mount points — use
it to drop one screw on its own. Static (no animation, no MQTT).

The canvas includes 40% padding around the head for the drop shadow, so the head
reads at `size_px`.

## Config

| key | meaning |
|-----|---------|
| `size_px` | head diameter in px (default 24) |
| `type` | `fillister` (domed) or `countersunk` |
| `finish` | `chrome`, `black`, or `custom` |
| `color` | hex (used when `finish` = `custom`) |
| `angle` | drive rotation in degrees |
| `damage` | 0–1 screwdriver slippage wear |
| `rust` | 0–1 oxide accumulation |

## Grab-bag sample

```json
{
  "Screw": {
    "type": "screw",
    "screw": {
      "size_px": 28,
      "type": "fillister",
      "finish": "chrome",
      "angle": 30,
      "damage": 0.2,
      "rust": 0.1
    }
  }
}
```
