# How to Use: The Layered Industrial Background Engine

This directory showcases the advanced procedural background engine used in the Open Air "Next Gen" interface. This engine generates photorealistic, resolution-independent industrial surfaces on the fly, simulating physical materials, manufacturing defects, and decades of wear.

## 1. Quick Start

To add a background to any GUI tab, add a `background` block at the root of your JSON file:

```json
{
  "background": {
    "type": "layered_industrial",
    "parameters": {
      "random_seed": 1234,
      "base_material": { "color": "#2a2a2a", "texture_type": "brushed" },
      "paint_layer": { "color": "#3a4a5a", "opacity": 0.9 },
      "screws": { "enabled": true },
      "metal_fold": { "enabled": true }
    }
  },
  "fields": { ... }
}
```

---

## 2. The Physics Stack

The engine renders layers in a specific physical order. Understanding this stack helps you predict how effects will look:

1.  **Substrate (Metal)**: The base raw material (Steel, Aluminum, Carbon).
2.  **Paint**: Applied *over* the substrate. Opacity determines how much metal grain shows through.
3.  **Damage (Chips)**: Scratches and edge wear physically remove the paint to reveal the substrate again.
4.  **Environmental**: Haze, Rust, Grime, and Dust settle on top of everything.
5.  **Hardware**: Screws and Metal Folds are structural elements added last.
6.  **Global Blur**: A final pass to blend digital sharpness into a photographic look.

---

## 3. Parameter Reference

### `base_material` (The Metal)
*   `color` (Hex): The color of the raw metal (e.g., `#444444` for steel, `#111111` for carbon).
*   `texture_type` (String):
    *   `flat`: Smooth, solid surface (good for plastics).
    *   `brushed`: Directional metal grain (Stainless Steel).
    *   `hammered`: Dimpled, beaten metal look (Industrial Test Equipment).
    *   `wrinkle`: Fine, high-frequency noise (Powder Coat).
    *   `enamel`: Slight "orange peel" wave (Vintage Consoles).
    *   `crosshatch`: Woven texture (Carbon Fiber).
*   `grain_intensity` (Float 0.0-1.0): How strong the texture is.
*   `grain_direction` (String): `vertical` or `horizontal` (for brushed/crosshatch).

### `paint_layer` (The Finish)
*   `color` (Hex): The paint color.
*   `opacity` (Float 0.0-1.0): `1.0` is solid paint. `0.0` is raw metal. `0.2` is a thin wash (anodized look).
*   `gradient_intensity` (Float 0.0-1.0): Adds a top-to-bottom light falloff to simulate room lighting.

### `metal_fold` (The Chassis)
Simulates 3D bent metal edges.
*   `enabled` (Bool): Turn on/off.
*   `width_px` (Int): Width of the fold in pixels (default `20`).
*   `creases` (List): Add internal seams for modular panels.
    ```json
    "creases": [
      { "position_pct": 0.33, "orientation": "vertical", "type": "valley" },
      { "position_pct": 0.50, "orientation": "horizontal", "type": "ridge" }
    ]
    ```

### `screws` (The Fasteners)
Adds Robertson (Square Drive) screws to the corners and midpoints.
*   `enabled` (Bool): Turn on/off.
*   `size_px` (Int): Head diameter (default `24`).
*   `rash` (Bool): Adds "Rack Rash" (circular scratches) around the hole.
*   `finish` (String): `chrome`, `black_oxide`, or `custom`.
*   `color` (Hex): Used if finish is `custom`.

### `edge_wear` (The Borders)
*   `enabled` (Bool): Turn on/off.
*   `fade_depth` (Int): Width of the vignette shadow in pixels.
*   `vignette_intensity` (Float 0.0-1.0): Darkness of the corners.
*   `scratch_depth` (Int): How far physical scratches extend from the edge.
*   `scratch_intensity` (Float): Amount of edge chipping.
*   `type` (String): `chipped` (hard edges) or `faded` (soft rub).

### `panel_scratches` (Surface Damage)
*   `count` (Int): Number of scratches.
*   `reveals_substrate` (Bool): If `true`, the scratch cuts through paint to show the metal color.
*   `intensity` (Float): Visibility of the scratch.
*   `depth_highlight` (Float): Strength of the white edge highlight (3D groove effect).

### `rust` (Corrosion)
*   `enabled` (Bool): Turn on/off.
*   `intensity` (Float): Amount of pitting and oxidation (Orange/Brown spots).

### `grime` (Dirt & Oil)
*   `stain_count` (Int): Number of oil/coffee blobs.
*   `stain_spread` (Int): Size of the blobs.
*   `color` (Hex): Color of the dirt (usually black or dark brown).
*   `opacity` (Float): Transparency of stains.

### `dust` (Particulates)
*   `enabled` (Bool): Turn on/off.
*   `intensity` (Float): Density of fine white/grey specks across the surface.

### `studio_haze` (Aging)
*   `enabled` (Bool): Turn on/off.
*   `intensity` (Float): Adds a warm yellow/brown multiply layer to simulate nicotine/UV aging.

### `global_blur` (The Secret Sauce)
*   `global_blur` (Float): Applies a Gaussian blur to the final image. **Crucial** for making procedural noise look like physical material. Recommended: `0.3` - `0.6`.

---

## 4. Integration with Meters

To make an instrument look like it is built *into* the panel (rather than sitting on top of it):

1.  **Transparent Assembly**: The engine automatically handles the area outside the bezel.
2.  **Transparent Face**: Set the meter's faceplate color to transparent.

```json
"Meter_1": {
  "type": "_NeedleVUMeter",
  "cosmetics": {
    "colors": {
        <-- THIS IS KEY
      "bezel": "#111111"
    }
  }
}
```

This tells the render engine to skip drawing the solid card, allowing your rust, scratches, and metal grain to show through the dial.


----------------- use this as a starting points:

{
  "background": {
    "type": "layered_industrial",
    "parameters": {
      "random_seed": 303,
      "global_blur": 0.8,
      "base_material": {
        "color": "#111111",
        "texture_type": "flat"
      },
      "paint_layer": {
        "color": "#223344",
        "opacity": 0.85,
        "gradient_intensity": 0.2
      },
      "rust": {
        "enabled": false
      },
      "edge_wear": {
        "enabled": true,
        "fade_depth": 15,
        "vignette_intensity": 0.4,
        "scratch_depth": 30,
        "scratch_intensity": 0.5
      },
      "grime": {
        "vignette_intensity": 0.4,
        "stain_count": 0
      },
      "dust": {
        "enabled": true,
        "intensity": 0.95
      },
      "screws": {
        "enabled": true,
        "finish": "custom",
        "color": "#223344"
      },
      "metal_fold": {
        "enabled": true,
        "width_px": 20
      },
      "panel_scratches": {
        "count": 5,
        "intensity": 0.2
      }
    }
  },
  "fields": {
    "Master_Meter": {
      "type": "_NeedleVUMeter",
      "label": "Master Studio Output",
      "geometry": { "width": 400, "height": 250 },
      "domain": {
        "primary": { "min": -20.0, "max": 3.0, "value_default": -7.0 }
      },
      "cosmetics": {
        "colors": { 
          "bezel": "#111111",
          "meter_face_colour": "transparent" 
        },
        "style_overrides": {
          "bezel_shape": "hotdog",
          "bezel_width": 8,
          "Pointer_Style": "knife-edge",
          "overlay_style": "dome"
        }
      }
    }
  }
}
