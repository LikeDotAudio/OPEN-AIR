# Reverb / Time-Domain FX Graph — Audit & Deployment Plan

**Author:** Claude (for Anthony Kuzub)
**Date:** 2026-07-06
**Target component:** `FrontEnd/libControl/graphing/Reverb/Reverb.jsx`
**Status:** Planning — directory `graphing/Reverb/` exists but is empty.

---

## 0. Executive Summary

You asked to add a **Reverb** tab that behaves like the two DSP visualizers already
in the app:

- Like **Equalization** (`graphing/Equalization/Equalization.jsx`): a live curve
  driven by MQTT knob topics, draggable handles, and **on-demand CSV + FIR export**.
- Like **DynamicsEnvelope** (`graphing/DynamicsEnvelope/DynamicsEnvelope.jsx`): a
  **time-domain envelope** graph (attack/hold/release) rendered from parameters.

A reverb is the natural marriage of both: it is fundamentally a **time-domain
impulse response (IR)** — a decaying envelope of reflections — that we also want to
**export as an FIR filter** (the IR *is* the FIR) and as a **CSV curve**. The math in
your paper (Schroeder comb + all-pass networks, feedforward/feedback delay lines,
discrete convolution) maps cleanly onto the existing patterns.

**Bottom line:** this is a well-scoped clone-and-extend job. No backend/Rust work is
required for the visualizer + export MVP. The one worthwhile refactor is to **extract
the FFT / window / download helpers currently trapped inside `Equalization.jsx` into a
shared `graphing/_dsp/` module** so Reverb, Delay, Flanger, and Chorus can all reuse
them instead of copy-pasting a radix-2 FFT four times.

---

## 1. Audit of the Source Material (the paper)

The paper is technically sound and college-accurate. Notes on what to **use as-is**,
what to **simplify**, and what to **flag** for a browser-side implementation:

| Claim in paper | Verdict | Implementation note |
|---|---|---|
| Direct → Early Reflections (10–80 ms) → Late Tail (RT60) three-phase model | ✅ Use as-is | This is the exact shape of our IR graph — mirrors the DynamicsEnvelope attack/hold/release skeleton. |
| Pre-Delay, Decay (RT60), Diffusion, Size as the 4 core params | ✅ Use as-is | These become the four MQTT knob topics (§6). |
| Feedback Comb Filter `y[n] = x[n-D] + g·y[n-D]` | ✅ Use as-is | Prime-number delay lengths; `g` derived from RT60 (§4). |
| Schroeder All-Pass `y[n] = -g·x[n] + x[n-D] + g·y[n-D]` | ✅ Use as-is | Series diffusers after the parallel comb bank. |
| Stability: `|g| < 1` or it "blows up" | ✅ **Critical guard** | Clamp `g ∈ (-0.999, 0.999)` before rendering the IR, else the export/plot NaNs out. Same class of bug as the EQ `log(0)` floor guard. |
| N = RT60 × fs taps (e.g. 96 000 taps for 2 s @ 48 k) | ⚠️ True but heavy | 96 k-tap `.fir` files are legitimate but large. Cap the **plotted** IR at a decimated preview (~2–4k points) while allowing the **exported** IR to be full length. Warn on tap counts > 65 536. |
| Time-domain convolution = 4.6 billion MAC/s → use FFT fast-convolution | ✅ Correct | We do **not** run convolution in the browser. We *synthesize the IR* (cheap) and hand the taps off as a file. Real-time convolution belongs in the Rust/backend engine, not the GUI. |
| 5.1 / True-Stereo decorrelated matrices (L→L, L→R, …) | ⚠️ Phase 2 | MVP ships **mono IR**. Stereo = two decorrelated IRs (offset prime delays); 5.1 = a channel selector. Schema already supports this via a `channels` selector (§6). Check the box, build it second. |
| Minimum-phase vs linear-phase tail | ✅ Reuse | `Equalization.generateFIR` already implements both (`phase: 'linear' | 'minimum'`) via real-cepstrum. Reverb IRs are naturally **minimum/causal** (energy front-loaded), so default `phase: 'minimum'`. |
| Damping = LPF inside the feedback loop (air/material absorption) | ✅ Use as-is | One-pole LPF coefficient per comb loop; exposed as a `Damping` knob (0–1 → HF rolloff per bounce). |
| 24-bit resolution matters so the tail decays smoothly (no "zipper"/truncation) | ✅ Note only | Export taps at `toFixed(10)` (same as EQ) — float text preserves the quiet tail. A WAV export would want 24/32-bit float; flagged as optional (§7). |

**Two mathematical cautions for the coder:**

1. **RT60 → feedback gain.** For a comb line of delay `D` samples at rate `fs`, the gain
   that yields a target `RT60` is `g = 10^(-3·D / (RT60·fs))`. This is the single most
   important formula and is *absent* from the paper — derive and centralize it.
2. **Diffusion vs Size vs Decay are coupled.** Size scales all `D`; Decay sets `g`;
   Diffusion sets the all-pass `g` and the number/spacing of combs. Keep them
   orthogonal in the UI even though the physics couples them, exactly like EQ keeps
   Freq/Gain/Q orthogonal per band.

---

## 2. Current Architecture — the Pattern We Clone

Findings from reading the live code (all paths under `FrontEnd/`):

### 2.1 Component contract
Every graph component is a Babel-in-browser React function stored on `window`:

```
const Reverb = ({ value: mqttData, config, topic }) => { ... };
window.Reverb = Reverb;
```

- **Rendering engines in use:** ECharts (`echarts.init(ref, 'dark')`) in
  `Equalization` / `AudioDynamics`; raw inline **SVG** in `DynamicsEnvelope`.
  → *Reverb should use ECharts* — we need log/decibel axes, draggable `graphic`
  handles, and the same export toolbar, all of which EQ already solves.

### 2.2 Three registration touch-points (the "add a component" checklist)
1. **`index.html`** (lines ~126–130): add
   `<script type="text/babel" src="./libControl/graphing/Reverb/Reverb.jsx?v=1"></script>`.
2. **`frameLayout/FieldComponent.jsx`** (line ~414): the dispatch `if` already matches
   `type.toLowerCase().includes('graph')`, but the explicit branch ladder needs a
   `type === '_Reverb'` arm that renders `window.Reverb`.
3. **JSON frame** under `Gui_Frames/…` uses `"type": "_Reverb"`; then **`update_tree.py`
   must be re-run** to embed it into `api/tree.json` (stale tree = stale UI — this is a
   known footgun, see the `gui-frames-tree-regen` memory).

### 2.3 MQTT data flow (declarative `topics` object)
The EQ graph is fully declarative (commit `0f51ffc7c`): the JSON supplies a `topics`
map, the component reads `window.useMqttMessages()`, and publishes via
`window.useMqttPublish()`:

```
"topics": { "PreDelay": "OpenAir/Gui/Rev_Params/PreDelay", ... }
```

- **⚠️ Inconsistency to avoid:** `AudioDynamics.jsx` calls `window.useMqttPublisher`
  (line 165) while `Equalization.jsx` calls `window.useMqttPublish` (line 431). EQ's is
  the one that actually works with drag-publish. **Reverb must use `useMqttPublish`.**

### 2.4 Live-curve → export bridge
EQ keeps `bandsRef` / `totalDataRef` refs updated inside the heavy MQTT effect so the
export buttons never fire off a stale closure (`Equalization.jsx:239-246, 644-645`).
Reverb replicates this with `paramsRef` / `irRef`.

### 2.5 Draggable handles
ECharts `graphic` circles with `convertToPixel` / `convertFromPixel`, a `draggingRef`
guard so the MQTT echo of our own publish doesn't fight the pointer, and a 40 ms
publish throttle (`Equalization.jsx:650-746`). Reverb reuses this verbatim for its
Pre-Delay / Decay handles on the IR plot.

---

## 3. Deployment Plan (phased)

### Phase 0 — Shared DSP extraction (refactor, unblocks all future FX) ✅ DONE
- [x] Create `graphing/_dsp/dsp.js` exporting `_fft`, `_besselI0`, `_windowVal`,
      `_downloadText` on a `window.OaDsp` namespace (+ reverb time-domain primitives).
- [ ] Point `Equalization.jsx` at `window.OaDsp` (deferred — EQ keeps its own copy for
      now; low-risk follow-up).
- [x] Add `<script>` for `_dsp/dsp.js` **before** the graph components in `index.html`.
- *Rationale:* Reverb, Delay, Flanger, Chorus will each need FFT + windowing + file
  download. Extract once now; four components stay thin.

### Phase 1 — Reverb visualizer MVP (mono) ✅ DONE
- [x] `Reverb/Reverb.jsx` — ECharts IR plot (time × amplitude, dB EDC overlay).
- [x] Read 4 knob topics (PreDelay, Decay/RT60, Diffusion, Size) + Damping + Mix.
- [x] Synthesize IR from a Schroeder network (§4) on every MQTT update.
- [x] Draggable Pre-Delay (x) and Decay (RT60) handles.
- [x] Register in `index.html` + `FieldComponent.jsx`.

### Phase 2 — Export toolbar (the part you specifically want) ✅ DONE (WAV deferred)
- [x] CSV button → IR + energy-decay curve (`TimeMs,Amplitude,DecayDb`, direct download).
- [x] FIR popover (Taps / Sample Rate / Phase / Window) → full-length IR `.fir`.
- [ ] Optional WAV export (24-bit) for convolution reverbs / DAWs — *not yet built.*

### Phase 3 — Sample frame + wiring ✅ DONE
- [x] `Gui_Frames/5_Samples/7_Reverb/Reverb.json` (graph + 6 param knobs).
- [x] Ran `python update_tree.py`; `api/tree.json` contains the new frame.
- [x] Changelog entry in `Documentation/Changelog/2026-07-06.md`.

### Phase 4 — Stereo / 5.1 + JFIR bundle ✅ DONE (sibling FX still stretch)
- [x] `channels` selector (Mono / Stereo / 5.1) → N decorrelated IRs
      (`synthesizeIRMulti` + `channelProfile`; C anchored, LFE damped, surrounds diffuse).
- [x] **JFIR** — shared `_dsp/jfir.js` (`window.OaJfir`) bundle format: params + per-channel
      FIR + curve CSV in one JSON. Used by **both Reverb and EQ**.
- [x] Reverb export: JFIR (all channels) / FIR (primary) / N× separate `.fir`.
- [x] Reverb IR & EDC visibility toggles.
- [ ] Fork the shared skeleton into `graphing/Delay/`, `graphing/Flanger/`,
      `graphing/Chorus/` (same delay-line math + JFIR export; still to build).

#### JFIR schema (v1)
```jsonc
{
  "format": "JFIR", "version": 1,
  "kind": "reverb" | "eq",
  "label": "Master Bus Reverb",
  "sampleRate": 48000,
  "parameters": { /* preset knobs, or EQ bands */ },
  "fir": {
    "taps": 4096, "phase": "minimum", "window": "hann",
    "channels": ["L","R","C","LFE","Ls","Rs"],
    "data": { "L": [ /* taps */ ], "R": [ ... ], ... }
  },
  "curve": { "columns": ["TimeMs","Amplitude","DecayDb"], "csv": "..." }
}
```

---

## 4. Pseudocode (relative to this project)

### 4.1 DSP core — Schroeder reverb IR synthesis (`_dsp` or in-component)

```js
// Target-RT60 → per-comb feedback gain. THE key formula (missing from the paper).
const rt60ToGain = (delaySamples, rt60Sec, fs) =>
    Math.pow(10, (-3 * delaySamples) / (rt60Sec * fs));

// One feedback comb with in-loop damping (one-pole LPF = air/material absorption).
//   y[n] = x[n-D] + g * lpf(y[n-D])
const combFilter = (input, D, g, damp) => {
    const out = new Float64Array(input.length);
    const buf = new Float64Array(D);      // circular delay line
    let idx = 0, lp = 0;
    for (let n = 0; n < input.length; n++) {
        const delayed = buf[idx];
        lp = (1 - damp) * delayed + damp * lp;   // one-pole LPF in the loop
        out[n] = delayed;
        buf[idx] = input[n] + g * lp;            // feed output back (clamp g < 1!)
        idx = (idx + 1) % D;
    }
    return out;
};

// Schroeder all-pass diffuser: y[n] = -g*x[n] + x[n-D] + g*y[n-D]
const allpassFilter = (input, D, g) => {
    const out = new Float64Array(input.length);
    const buf = new Float64Array(D);
    let idx = 0;
    for (let n = 0; n < input.length; n++) {
        const delayed = buf[idx];
        const y = -g * input[n] + delayed;
        buf[idx] = input[n] + g * y;
        out[n] = y;
        idx = (idx + 1) % D;
    }
    return out;
};

// Build the full impulse response from UI params. Returns Float64Array of taps.
//   params = { preDelayMs, rt60Sec, diffusion(0..1), size(0..1), damping(0..1) }
const synthesizeIR = (params, fs, maxTaps) => {
    const N = Math.min(maxTaps, Math.ceil(params.rt60Sec * fs) + preDelaySamples);
    const impulse = new Float64Array(N);
    const preDelaySamples = Math.round(params.preDelayMs * 1e-3 * fs);
    impulse[preDelaySamples] = 1;                 // unit impulse after pre-delay

    // 4–8 parallel combs at prime-number delays, scaled by Size.
    const PRIMES = [1557, 1617, 1491, 1422, 1277, 1356, 1188, 1116];
    const sizeScale = 0.5 + params.size;          // 0.5x .. 1.5x room
    let tail = new Float64Array(N);
    PRIMES.forEach(p => {
        const D = Math.max(1, Math.round(p * sizeScale));
        let g = rt60ToGain(D, params.rt60Sec, fs);
        g = Math.max(-0.999, Math.min(0.999, g)); // STABILITY CLAMP
        const c = combFilter(impulse, D, g, params.damping);
        for (let n = 0; n < N; n++) tail[n] += c[n] / PRIMES.length;
    });

    // Series all-passes → diffusion (smooths the metallic comb ringing).
    const APS = [225, 556, 441, 341];
    const apG = 0.5 + 0.2 * params.diffusion;
    APS.forEach(D => { tail = allpassFilter(tail, Math.round(D * sizeScale), apG); });

    return tail;   // this IS the FIR — plot it, export it.
};
```

### 4.2 Component skeleton (mirrors `Equalization.jsx`)

```jsx
const Reverb = ({ value: mqttData, config, topic }) => {
    const chartRef = React.useRef(null), chartInstance = React.useRef(null);
    const paramsRef = React.useRef({});    // live params → export handlers (no stale closure)
    const irRef = React.useRef(new Float64Array(0));
    const draggingRef = React.useRef(false), lastPubRef = React.useRef(0);

    // FIR export config (identical control set to EQ)
    const [firTaps, setFirTaps]       = React.useState(4096);
    const [firSampleRate, setFirRate] = React.useState(48000);
    const [firPhase, setFirPhase]     = React.useState('minimum'); // reverb = causal
    const [firWindow, setFirWindow]   = React.useState('hann');
    const [showFirDialog, setShow]    = React.useState(false);

    const messages  = (window.useMqttMessages && window.useMqttMessages()) || {};
    const publishFn = window.useMqttPublish ? window.useMqttPublish() : null; // NOT Publisher

    // ---- init ECharts once (time x-axis ms, amplitude/dB y-axis) ----
    React.useEffect(() => { /* echarts.init + static option, see EQ:310-428 */ }, [cfgKey]);

    // ---- on every MQTT tick: read topics → synth IR → plot + refs ----
    React.useEffect(() => {
        const p = {
            preDelayMs: readTopic('PreDelay', 20),
            rt60Sec:    readTopic('Decay', 1.8),
            diffusion:  readTopic('Diffusion', 0.7),
            size:       readTopic('Size', 0.5),
            damping:    readTopic('Damping', 0.3),
        };
        const ir = synthesizeIR(p, 48000, 96000);
        paramsRef.current = p; irRef.current = ir;
        chartInstance.current.setOption({ series: [
            { name: 'IR',  type: 'line', data: decimate(ir, 3000), ... },
            { name: 'EDC', type: 'line', data: energyDecayCurve(ir), ... }, // Schroeder integral
        ]});
        // draggable PreDelay/Decay handles — clone EQ:650-746 (draggingRef + 40ms throttle)
    }, [messages, mqttData, config?.command]);

    // ---- exports ----
    const handleExportFIR = () => {
        // Option A: export the synthesized IR directly (already the taps we plotted).
        // Option B: re-render at the chosen fs/taps for sample-accurate output.
        const ir = synthesizeIR(paramsRef.current, parseInt(firSampleRate), parseInt(firTaps));
        let s = ''; for (let i = 0; i < ir.length; i++) s += ir[i].toFixed(10) + '\n';
        window.OaDsp._downloadText(s, 'reverb_ir.fir', 'text/plain;charset=utf-8;');
    };
    const handleExportCSV = () => {
        let csv = 'TimeMs,Amplitude,DecayDb\n';
        const edc = energyDecayCurve(irRef.current);
        irRef.current.forEach((a, n) => { csv += `${(n/48).toFixed(3)},${a.toFixed(8)},${edc[n].toFixed(3)}\n`; });
        window.OaDsp._downloadText(csv, 'reverb_curve.csv', 'text/csv;charset=utf-8;');
    };

    return (/* chart div + top-right FIR▾ / CSV buttons + FIR popover — copy EQ:758-810 */);
};
window.Reverb = Reverb;
```

### 4.3 Energy Decay Curve (the CSV's "nice" column — Schroeder backward integral)

```js
// EDC[n] = 10·log10( Σ_{k>=n} ir[k]^2  /  Σ_{k} ir[k]^2 ) — the smooth RT60 line.
const energyDecayCurve = (ir) => {
    const edc = new Float64Array(ir.length);
    let running = 0;
    for (let n = ir.length - 1; n >= 0; n--) { running += ir[n]*ir[n]; edc[n] = running; }
    const total = edc[0] || 1e-12;
    for (let n = 0; n < ir.length; n++) edc[n] = 10 * Math.log10(Math.max(edc[n]/total, 1e-12));
    return edc;
};
```

---

## 5. Library Components — Existing vs. New

### ✅ Already exist — reuse directly
- **ECharts** (global `echarts`) — same dark-theme init, log/value axes, draggable
  `graphic` circles, `convertToPixel`/`convertFromPixel`.
- **MQTT hooks** — `window.useMqttMessages()`, `window.useMqttPublish()`,
  `window.useMqttLang()`.
- **`_downloadText(content, filename, mime)`** — the browser-download helper
  (`Equalization.jsx:220`).
- **Radix-2 FFT `_fft`, Kaiser `_besselI0`, `_windowVal`, `generateFIR`** — the entire
  frequency-sampling FIR pipeline (`Equalization.jsx:87-217`). Reverb's linear-phase
  export path can call `generateFIR` directly; the min-phase synthesis is native.
- **FIR popover UI** (Taps/SampleRate/Phase/Window dropdowns + styles
  `iconBtn`/`ctrlSelect`/`ctrlLabel`) — copy the JSX block wholesale.
- **`_CustomLTP`, `_Knob`, `SelectorSwitch`** widgets — for the parameter knobs in the
  JSON frame (Pre-Delay, Decay, Diffusion, Size, Damping, Mix, Channels selector).

### ☐ New elements to build (check the box)
- [ ] **`graphing/_dsp/dsp.js`** — shared namespace (`window.OaDsp`) hosting the FFT /
      window / download helpers extracted from EQ. *One-time, unblocks all FX.*
- [ ] **`synthesizeIR`, `combFilter`, `allpassFilter`, `rt60ToGain`,
      `energyDecayCurve`, `decimate`** — reverb DSP (new; §4). Put the reusable delay
      primitives in `_dsp` too — Delay/Flanger/Chorus need them.
- [ ] **`Reverb/Reverb.jsx`** — the component itself.
- [ ] **`Reverb/Readme.md`** — match the per-component Readme convention.
- [ ] *(Phase 2)* **WAV encoder** (`floatTo24BitWav`) if we want DAW-ready IR files, not
      just `.fir` text. Small (~40 lines), no dependency.
- [ ] *(Phase 4)* **Stereo/5.1 decorrelator** — offsets prime delays per channel.

### ↔ Recommended refactor
Extracting the EQ DSP into `_dsp` is the highest-leverage move: it removes a future
4× copy of a non-trivial radix-2 FFT and makes Reverb/Delay/Flanger/Chorus thin
UI-over-shared-DSP components. Low risk — keep local fallbacks in EQ so nothing breaks
if the script load order regresses.

---

## 6. JSON Schema Support

The declarative `topics`-object pattern (EQ, commit `0f51ffc7c`) already supports
everything Reverb needs. A `_Reverb` graph node + a block of standard knobs:

```jsonc
"Reverb_Graph": {
  "type": "_Reverb",
  "label": { "En": "Convolution / Algorithmic Reverb" },
  "topics": {
    "PreDelay":  "OpenAir/Gui/Rev_Params/PreDelay",
    "Decay":     "OpenAir/Gui/Rev_Params/Decay",
    "Diffusion": "OpenAir/Gui/Rev_Params/Diffusion",
    "Size":      "OpenAir/Gui/Rev_Params/Size",
    "Damping":   "OpenAir/Gui/Rev_Params/Damping",
    "Mix":       "OpenAir/Gui/Rev_Params/Mix"
  },
  "channels": "mono",          // "mono" | "stereo" | "5.1"  (Phase 4)
  "fir_defaults": {            // seed the export popover from the frame
    "taps": 4096, "sample_rate": 48000, "phase": "minimum", "window": "hann"
  },
  "geometry": { "width": "100%", "height": 400 }
}
```

Companion knobs use the existing `_Knob` widget (domain pillar = min/max/default),
e.g. Pre-Delay 0–200 ms, Decay/RT60 0.1–10 s (log), Diffusion 0–1, Size 0–1,
Damping 0–1, Mix 0–100 %. A `SelectorSwitch` supplies the `Channels` mode. All of
these already render today — no new widget types required for the knobs.

**Schema additions that are genuinely new (small, optional):**
- `channels` (string enum) — read by the component to decide how many IRs to synth.
- `fir_defaults` (object) — lets a frame preset the export dialog (EQ currently
  hardcodes its defaults in state; wiring this makes it declarative for both).

**Reminder:** after adding the frame JSON, run `python update_tree.py` so
`api/tree.json` picks it up — the app renders from the embedded tree, not the raw
frame files (`gui-frames-tree-regen` memory).

---

## 7. Export Functionality — CSV + FIR "on demand" (the priority feature)

You specifically value how EQ exports a CSV curve and an FIR on demand. Reverb inherits
the exact same toolbar (top-right `FIR ▾` / `CSV` pills, `_downloadText`), with
reverb-appropriate payloads:

- **CSV** — `TimeMs, Amplitude, DecayDb` per tap (IR sample + Schroeder EDC). Direct
  download, no dialog. Good for Excel/plotting and for eyeballing RT60.
- **FIR** — the synthesized impulse response written one tap per line at `toFixed(10)`.
  This *is* the convolution kernel `h[k]` from the paper's `y[n]=Σ h[k]x[n-k]`; drop it
  straight into a convolution reverb or the Rust engine. Popover exposes Taps / Sample
  Rate / Phase / Window (reuses EQ's controls).
- **WAV (optional, Phase 2)** — 24-bit/32-float `.wav` of the same taps, for loading
  into commercial convolution plugins / DAWs. The paper's 24-bit note is exactly why:
  float/24-bit preserves the quiet tail without zipper/truncation artifacts.

This export contract is the reusable backbone for **Delay, Flanger, and Chorus** — each
is a delay-line IR with different modulation, so each ships the same CSV+FIR buttons
over the same `_dsp` helpers. Building it cleanly once for Reverb pays off four times.

---

## 8. Risks & Watch-items

1. **Stability clamp** on feedback gain `g` — non-negotiable; unclamped `|g|≥1`
   produces `Inf`/`NaN` taps that break both the plot and the file.
2. **Large tap counts** — 2 s @ 96 k = 96 000 taps. Decimate for the *plot*
   (`decimate(ir, ~3000)`); export full. Warn above 65 536.
3. **`useMqttPublish` vs `useMqttPublisher`** — use the former (EQ's working hook), not
   AudioDynamics' typo'd one.
4. **Tree regen** — forgetting `update_tree.py` = stale UI; the #1 recurring footgun in
   this project.
5. **Script load order** — `_dsp/dsp.js` must load *before* `Reverb.jsx` in
   `index.html`; keep local fallbacks so a regression degrades gracefully.
6. **Real-time convolution stays in the backend** — the GUI only *synthesizes and
   exports* the kernel; it must never attempt the 4.6-GMAC/s convolution the paper
   describes.

---

## Appendix A — Files to touch

| File | Change |
|---|---|
| `graphing/_dsp/dsp.js` | **new** — shared FFT/window/download + delay primitives |
| `graphing/Reverb/Reverb.jsx` | **new** — the component |
| `graphing/Reverb/Readme.md` | **new** — component doc |
| `graphing/Equalization/Equalization.jsx` | edit — source `window.OaDsp` (fallbacks kept) |
| `index.html` | edit — `<script>` tags for `_dsp/dsp.js` + `Reverb.jsx` |
| `frameLayout/FieldComponent.jsx` | edit — add `type === '_Reverb'` render arm (~line 414) |
| `Gui_Frames/5_Samples/7_Reverb/Reverb.json` | **new** — sample frame |
| `api/tree.json` | regenerated — `python update_tree.py` |
| `Documentation/Changelog/2026-07-06.md` | edit — log the work |
