# Implementation Guide: OcaBin Elastic Viewport
**Module:** `async_grid_renderer.py`  
**Widget Type:** `OcaBin`, `Bin`

## 1. Architecture Overview
The `OcaBin` is an explicit root-level or structural container that utilizes a **Canvas Viewport Triad** to handle dynamic layout overflow. Unlike standard frames that squash or clip content uncontrollably, `OcaBin` bounds its content elastically, providing scrollbars only when explicitly required by the physical window size.

### The Viewport Triad:
1.  **The Outer Hull:** A base frame pinned to its container (e.g., `NSEW`). It scales perfectly with the parent window or cell.
2.  **The Viewport:** A `tk.Canvas` placed inside the hull. This acts as the clipping region ("the window" the user looks through).
3.  **The Content Payload:** An inner frame placed inside the canvas. All child `OcaBlocks` and widgets are packed here.

## 2. Overflow Trigger Logic
The engine binds a `<Configure>` event to the Canvas and Inner frame. Every time the user resizes the window, the engine compares the required dimensions of the payload against the available viewport dimensions. 

Scrollbars are dynamically mapped to the grid based on the `behavior` parameters:
- `auto`: The scrollbar only appears if the payload breaches the viewport boundary.
- `allow`: The scrollbar is perpetually drawn, even if disabled/unnecessary.
- `deny`: The scrollbar is never drawn, forcing the viewport to absolutely clip the content.

## 3. Detailed Parameter Breakdown

### 3.1 Primary Parameters
| Parameter | Type | Description |
| :--- | :--- | :--- |
| `type` | String | Must be `OcaBin` or `Bin`. |
| `fields` | Object | Standard dictionary of child blocks/widgets. |

### 3.2 `geometry` (The Bounds)
| Sub-Parameter | Type | Description |
| :--- | :--- | :--- |
| `anchor` | String | Standard layout anchoring (e.g., `NSEW`, `center`). |
| `min_width` | Int | Optional. The minimum width before triggering EW overflow. |
| `min_height` | Int | Optional. The minimum height before triggering NS overflow. |

### 3.3 `behavior` (The Overflow)
| Sub-Parameter | Type | Description |
| :--- | :--- | :--- |
| `overflow_ns` | Enum | Vertical overflow logic: `auto`, `allow`, `deny`. |
| `overflow_ew` | Enum | Horizontal overflow logic: `auto`, `allow`, `deny`. |

## 4. Full Implementation Example
```json
{
  "Master_Layout_Bin": {
    "type": "OcaBin",
    "description": "Root container locked to window edges with responsive NS overflow.",
    "geometry": {
      "anchor": "NSEW"
    },
    "behavior": {
      "overflow_ns": "auto",  
      "overflow_ew": "deny"   
    },
    "fields": {
      "Control_Panel_Block": {
        "type": "OcaBlock",
        "fields": {
           "Example_Widget": { "type": "_SmartFader" }
        }
      }
    }
  }
}
```
