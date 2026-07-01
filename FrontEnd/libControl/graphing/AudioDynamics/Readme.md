# AudioDynamics Graph

A specialized graph for displaying dynamics processing curves (Compressor, Expander, Gate). It features a 1:1 reference line and a customizable dynamic response curve. Both axes represent dB (-90 to 0).

- **Defines:** `AudioDynamics`
- **Props:** `value`, `config`
- **MQTT:** Listens for curve point updates.

<!-- wysiwyg:sample -->
## Sample (WYSIWYG library source)

```json
{
  "AudioDynamics_Example": {
    "type": "_AudioDynamics",
    "identity": {
      "label": "Stagebox Mic 53",
      "id": "dynamics_graph"
    },
    "geometry": {
      "width": 400,
      "height": 400
    },
    "domain": {
      "primary": {
        "value_default": ""
      }
    },
    "datasets": [
      {
        "id": "curve",
        "initial_csv_data": "x,y\n-90,-90\n-40,-40\n-20,-20\n0,-12"
      }
    ],
    "layout": {
      "sticky": "nw",
      "padx": 10,
      "pady": 10
    }
  },
  "_README": "AudioDynamics renders a standard compressor/expander transfer curve. It is pre-styled and scaled for audio levels in dBFS."
}
```
