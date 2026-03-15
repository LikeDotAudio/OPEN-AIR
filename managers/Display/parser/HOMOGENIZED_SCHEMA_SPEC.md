# OPEN-AIR Homogenized Schema Specification

This document defines the universal standard for all JSON declarations within the OPEN-AIR framework. Adherence to this specification ensures high performance, predictable parsing, and system-wide scalability.

## 🏛️ The Five-Pillar Architecture

Every widget, container, or data structure must strictly declare these five pillars. If a pillar is not used, it must be an empty object `{}`.

1.  **`identity`**: Metadata for identification and classification.
2.  **`geometry`**: Spatial properties, layout, and grid positioning.
3.  **`domain`**: Functional state, ranges, limits, and units.
4.  **`dynamics`**: I/O, telemetry (MQTT), polling, and event logic.
5.  **`cosmetics`**: Visual aesthetics, colors, textures, and typography.

---

## 📖 Lexicon Dictionary (Universal Abbreviations)

To reduce payload size and eliminate string parsing overhead, use these standard abbreviations. **All numeric values must be naked integers or floats (no unit strings like "px" or "ms").**

| Key | Abbreviation | Implied Unit | Pillar | Description |
| :--- | :--- | :--- | :--- | :--- |
| **id** | `id` | - | identity | Unique identifier. |
| **type** | `type` | - | identity | Widget class/type string. |
| **label** | `lbl` | - | identity | Human-readable name. |
| **width** | `w` | pixels | geometry | Horizontal dimension. |
| **height** | `h` | pixels | geometry | Vertical dimension. |
| **x-pos** | `x` | pixels | geometry | Horizontal offset. |
| **y-pos** | `y` | pixels | geometry | Vertical offset. |
| **padding** | `pad` | pixels | geometry | Internal margin. |
| **value** | `val` | float/int | domain | Current functional state. |
| **minimum** | `min` | float/int | domain | Lower threshold. |
| **maximum** | `max` | float/int | domain | Upper threshold. |
| **unit** | `unit` | string | domain | Engineering unit (e.g., "dBm", "Hz"). |
| **subscribe** | `sub` | topic string | dynamics | Inbound MQTT topic. |
| **publish** | `pub` | topic string | dynamics | Outbound MQTT topic. |
| **polling** | `poll` | milliseconds | dynamics | Refresh/poll interval. |
| **background**| `bg` | color hex | cosmetics | Background color. |
| **foreground**| `fg` | color hex | cosmetics | Foreground/text color. |

---

## 🏗️ Base Widget Template (JSON)

```json
{
  "identity": {
    "id": "unique_id",
    "type": "_WidgetType",
    "lbl": "Widget Label"
  },
  "geometry": {
    "w": 300,
    "h": 200,
    "x": 0,
    "y": 0,
    "pad": 10
  },
  "domain": {
    "val": 0.0,
    "min": 0.0,
    "max": 100.0,
    "unit": "unit"
  },
  "dynamics": {
    "sub": "topic/in",
    "pub": "topic/out",
    "poll": 100
  },
  "cosmetics": {
    "bg": "#121212",
    "fg": "#FFFFFF",
    "style": {}
  }
}
```

---

## 🔗 Groupings and Child Arrays

For any container component (Blocks, Arrays, Tables), nested elements must be declared in an `items` array at the root level.

```json
{
  "identity": { "type": "OcaBlock", "id": "my_block" },
  "items": [
    { "identity": { "type": "_GuiButton", "id": "btn_1" }, ... },
    { "identity": { "type": "_GuiButton", "id": "btn_2" }, ... }
  ],
  "geometry": {},
  "domain": {},
  "dynamics": {},
  "cosmetics": {}
}
```

## 📜 Implementation Rules

1.  **No Naked Properties**: Every property must reside within one of the five pillars or the `items` array.
2.  **Strict Typing**: Do not stringify numbers. `100` is an integer, `"100"` is a string error.
3.  **Implied Units**: Never include units in values. `w: 100` is correct. `w: "100px"` is invalid.
4.  **Empty Pillars**: Always include all five pillars, even if they are empty objects `{}`.
