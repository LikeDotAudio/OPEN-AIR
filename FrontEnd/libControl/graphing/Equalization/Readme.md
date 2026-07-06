# Equalization Graph

A specialized graph for displaying frequency equalization curves (EQ). It features a log-scale frequency X-axis (20Hz to 20kHz) and a linear amplitude Y-axis (-32dB to +32dB) with a smooth interpolation line.

- **Defines:** `Equalization`
- **Props:** `value`, `config`
- **MQTT:** Listens for curve point updates.

## Export toolbar

Above the graph is a toolbar for exporting the current curve:

- **Export CSV** — the summed magnitude response as `Freq,Gain` rows (`eq_curve.csv`).
- **Export FIR** — the curve realised as an FIR impulse response (`eq_filter.fir`,
  one coefficient per line) via the frequency-sampling method (target magnitude →
  IFFT → window). Configured by four dropdowns:
  - **Taps** — filter length / number of coefficients (512–16384). More taps trace
    sharp, low-frequency moves accurately at the cost of latency and CPU.
  - **Sample Rate** — the target `fs` (44.1–192 kHz). Digital filters only know
    normalized frequency, so this must match the audio the filter runs on or the
    whole curve shifts in pitch.
  - **Phase** — `Linear` (exact symmetric taps, zero phase distortion, N/2 latency,
    can pre-ring) or `Minimum` (real-cepstrum reconstruction: no pre-ringing,
    front-loaded energy, mimics analog EQ).
  - **Window** — taper applied when truncating: `Hann`, `Hamming`, `Blackman`,
    `Kaiser` (β=8), or `Rectangular` (no taper — expect ripple).

<!-- wysiwyg:sample -->
## Sample (WYSIWYG library source)

```json
{
  "Equalization_Example": {
    "type": "_Equalization",
    "identity": {
      "label": "Stagebox Mic 53",
      "id": "eq_graph"
    },
    "geometry": {
      "width": 500,
      "height": 350
    },
    "domain": {
      "primary": {
        "value_default": ""
      }
    },
    "datasets": [
      {
        "id": "eq_curve",
        "initial_csv_data": "x,y\n20,-32\n50,-10\n100,3\n150,2\n200,0\n300,-8\n500,-1\n1000,2\n2000,1\n5000,4\n10000,1\n20000,0"
      }
    ],
    "layout": {
      "sticky": "nw",
      "padx": 10,
      "pady": 10
    }
  },
  "_README": "Equalization renders a standard EQ response curve. It is pre-styled and scaled for audio frequencies (20-20k) and dB amplitude (-32 to 32)."
}
```
