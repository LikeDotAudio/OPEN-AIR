# Reverb

Live reverb **impulse-response (IR)** visualizer with on-demand **FIR** and **CSV**
export. Mirrors the Equalization component: MQTT-driven, draggable handles, and the
same top-right export toolbar.

## What it draws

- **IR (orange, left axis):** the synthesized impulse response — a unit impulse fed
  through a Schroeder network (parallel feedback combs → series all-pass diffusers).
  Peak-decimated to ~3000 points for the plot.
- **EDC (green, right axis, dB):** the Schroeder backward-integrated energy decay
  curve — the smooth line whose slope is RT60.

## Parameters (MQTT topics)

Supplied declaratively via the JSON `topics` map (falls back to
`OpenAir/Gui/<command>/<Key>`):

| Key | Meaning | Typical range |
|---|---|---|
| `PreDelay` | gap before first reflection (ms) | 0–200 |
| `Decay` | RT60 tail length (s) | 0.1–10 |
| `Diffusion` | all-pass density (0–1) | 0–1 |
| `Size` | room scale, scales all delays (0–1) | 0–1 |
| `Damping` | in-loop HF absorption (0–1) | 0–1 |
| `Mix` | wet/dry (%) — informational in the graph | 0–100 |

## Draggable handles

- **Orange** handle → Pre-Delay (drag horizontally).
- **Green** handle → Decay/RT60 (drag horizontally along the −60 dB line).

Publishes throttled at 40 ms with a `draggingRef` guard so the MQTT echo of our own
publish doesn't fight the pointer (same pattern as EQ).

## Channels (Mono / Stereo / 5.1)

Layout comes from the MQTT `Channels` topic (`Mono` / `Stereo` / `5.1`), falling back
to `config.channels`, then mono. Each channel is a **decorrelated** IR (distinct delay
scale + pre-delay offset). Roles in 5.1: **L/R** offset pair, **C** anchored & drier,
**LFE** heavily damped, **Ls/Rs** later + more diffuse. Every channel plots as its own
colored trace with a legend.

## Trace toggles

Toolbar **IR** and **EDC** pills (highlighted when on) show/hide each trace — e.g. turn
the IR off to read the decay envelope alone.

## Export

- **CSV** → `TimeMs, Amplitude, DecayDb` for the primary channel.
- **FIR ▾** → popover (Taps / Sample Rate / Phase / Window) with three export modes:
  - **JFIR** — one `.jfir` JSON bundle: params + **every** channel's FIR + curve CSV
    (see `../_dsp/jfir.js`). The canonical multichannel export.
  - **FIR** — the primary channel only, plain `.fir` (one tap per line, `toFixed(10)`).
    The IR **is** the convolution kernel `h[k]`.
  - **N× separate .fir** (multichannel only) — one `.fir` file per channel.
  Default phase is **minimum** (reverb IRs are causal).

## DSP

All math lives in `../_dsp/dsp.js` (`window.OaDsp`): `synthesizeIR`, `combFilter`,
`allpassFilter`, `rt60ToGain`, `energyDecayCurve`, `decimate`, plus the shared FFT /
window / download helpers. The component keeps minimal local fallbacks so a
script-load-order regression degrades gracefully.

## Wiring checklist

1. `index.html` — `<script>` for `_dsp/dsp.js` then `Reverb/Reverb.jsx`.
2. `frameLayout/FieldComponent.jsx` — `type === '_Reverb'` render arm.
3. Frame JSON uses `"type": "_Reverb"`; run `python update_tree.py` after editing.
