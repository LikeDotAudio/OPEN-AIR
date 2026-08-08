/**
 * Header: dsp.js
 * Purpose: Shared DSP helpers for the graphing components (EQ, Reverb, Delay,
 *          Flanger, Chorus).
 * Description: Frequency-domain primitives (radix-2 FFT, windows) extracted from
 *          Equalization.jsx so every FX visualizer shares one implementation, plus
 *          time-domain primitives (delay lines, Schroeder comb/all-pass, reverb IR
 *          synthesis) and the browser file-download helper.
 *
 * Everything is attached to window.OaDsp. Components keep local fallbacks so a
 * script-load-order regression degrades gracefully rather than throwing.
 *
 * Version: 26.07.06.1
 * Change Log:
 * - 2026-07-06: Initial extraction from Equalization.jsx + new reverb primitives.
 */

(function () {
    // -----------------------------------------------------------------------
    // Frequency-domain primitives (moved verbatim from Equalization.jsx)
    // -----------------------------------------------------------------------

    // In-place iterative radix-2 FFT. Length must be a power of two.
    // inverse=true performs the IFFT (and divides by N).
    const _fft = (re, im, inverse) => {
        const n = re.length;
        if (n <= 1) return;
        // Bit-reversal permutation
        for (let i = 1, j = 0; i < n; i++) {
            let bit = n >> 1;
            for (; j & bit; bit >>= 1) j ^= bit;
            j ^= bit;
            if (i < j) {
                const tr = re[i]; re[i] = re[j]; re[j] = tr;
                const ti = im[i]; im[i] = im[j]; im[j] = ti;
            }
        }
        for (let len = 2; len <= n; len <<= 1) {
            const ang = (inverse ? 2 : -2) * Math.PI / len;
            const wr = Math.cos(ang), wi = Math.sin(ang);
            for (let i = 0; i < n; i += len) {
                let cwr = 1, cwi = 0;
                for (let k = 0; k < len / 2; k++) {
                    const a = i + k, b = i + k + len / 2;
                    const xr = re[b] * cwr - im[b] * cwi;
                    const xi = re[b] * cwi + im[b] * cwr;
                    re[b] = re[a] - xr; im[b] = im[a] - xi;
                    re[a] += xr;        im[a] += xi;
                    const ncwr = cwr * wr - cwi * wi;
                    cwi = cwr * wi + cwi * wr;
                    cwr = ncwr;
                }
            }
        }
        if (inverse) {
            for (let i = 0; i < n; i++) { re[i] /= n; im[i] /= n; }
        }
    };

    // Modified Bessel function I0 (series) for the Kaiser window.
    const _besselI0 = (x) => {
        let sum = 1, term = 1;
        for (let k = 1; k < 30; k++) {
            term *= (x * x) / (4 * k * k);
            sum += term;
            if (term < 1e-12 * sum) break;
        }
        return sum;
    };

    // Symmetric window value at sample n of a length-N window.
    const _windowVal = (type, n, N) => {
        const M = N - 1;
        if (M <= 0) return 1;
        switch (type) {
            case 'rect':     return 1;
            case 'hann':     return 0.5 - 0.5 * Math.cos(2 * Math.PI * n / M);
            case 'hamming':  return 0.54 - 0.46 * Math.cos(2 * Math.PI * n / M);
            case 'blackman': return 0.42 - 0.5 * Math.cos(2 * Math.PI * n / M) + 0.08 * Math.cos(4 * Math.PI * n / M);
            case 'kaiser': {
                const beta = 8.0;
                const r = (2 * n / M) - 1; // -1..1
                return _besselI0(beta * Math.sqrt(Math.max(0, 1 - r * r))) / _besselI0(beta);
            }
            default: return 1;
        }
    };

    // -----------------------------------------------------------------------
    // File download helper
    // -----------------------------------------------------------------------

    // Trigger a browser download for generated text content.
    const _downloadText = (content, filename, mime) => {
        const blob = new Blob([content], { type: mime });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    // -----------------------------------------------------------------------
    // Time-domain primitives (delay lines / Schroeder reverb network)
    // Shared by Reverb and, later, Delay / Flanger / Chorus.
    // -----------------------------------------------------------------------

    // Target-RT60 -> per-comb feedback gain. For a comb line of `delaySamples`
    // at rate `fs`, this is the feedback gain whose repeated multiplication decays
    // by 60 dB over `rt60Sec`. (The one formula the source paper omits.)
    const rt60ToGain = (delaySamples, rt60Sec, fs) => {
        if (!(rt60Sec > 0) || !(fs > 0) || delaySamples <= 0) return 0;
        return Math.pow(10, (-3 * delaySamples) / (rt60Sec * fs));
    };

    // Clamp feedback gain into the stable open interval. |g| >= 1 blows the
    // recursion up to Inf/NaN and poisons both the plot and the exported taps.
    const clampGain = (g) => Math.max(-0.999, Math.min(0.999, g));

    // Feedback comb with a one-pole low-pass in the loop (air/material damping):
    //   lp    = (1-damp)*delayed + damp*lp
    //   out   = delayed
    //   buf   = x[n] + g*lp
    const combFilter = (input, D, g, damp) => {
        const out = new Float64Array(input.length);
        if (D <= 0) return out;
        const buf = new Float64Array(D); // circular delay line
        let idx = 0, lp = 0;
        const d = Math.max(0, Math.min(0.999, damp || 0));
        for (let n = 0; n < input.length; n++) {
            const delayed = buf[idx];
            lp = (1 - d) * delayed + d * lp;
            out[n] = delayed;
            buf[idx] = input[n] + g * lp;
            idx = (idx + 1) % D;
        }
        return out;
    };

    // Schroeder all-pass diffuser: y[n] = -g*x[n] + x[n-D] + g*y[n-D].
    // Preserves magnitude response while scrambling phase -> smooths comb ringing.
    const allpassFilter = (input, D, g) => {
        const out = new Float64Array(input.length);
        if (D <= 0) return out;
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

    // Prime-ish base delays (samples @ 48 kHz) for a Schroeder/Freeverb-style bank.
    const COMB_DELAYS = [1557, 1617, 1491, 1422, 1277, 1356, 1188, 1116];
    const ALLPASS_DELAYS = [225, 556, 441, 341];

    // Build a reverb impulse response from UI parameters. Returns a Float64Array of
    // taps (this IS the FIR: plot it, export it).
    //   params  = { preDelayMs, rt60Sec, diffusion(0..1), size(0..1), damping(0..1) }
    //   profile = optional per-channel decorrelation shim (see channelProfile):
    //     { delayScale, extraPreMs, diffusionBoost, dampingBoost, gainScale }
    const synthesizeIR = (params, fs, maxTaps, profile) => {
        fs = fs || 48000;
        maxTaps = maxTaps || 96000;
        const p = params || {};
        const pr = profile || {};
        const rt60Sec   = (p.rt60Sec   > 0) ? p.rt60Sec   : 1.8;
        const diffusion = clamp01(p.diffusion, 0.7);
        const size      = clamp01(p.size, 0.5);
        const damping   = clamp01(p.damping, 0.3);

        // Per-channel shims (default to identity for mono).
        const delayScale     = (pr.delayScale > 0) ? pr.delayScale : 1;
        const extraPreMs     = pr.extraPreMs || 0;
        const diffusionBoost = pr.diffusionBoost || 0;
        const dampUse        = Math.max(0, Math.min(0.999, damping + (pr.dampingBoost || 0)));
        const gainScale      = (pr.gainScale === undefined) ? 1 : pr.gainScale;

        const preDelaySamples = Math.max(0, Math.round(((p.preDelayMs || 0) + extraPreMs) * 1e-3 * fs));

        // Length: pre-delay + the decay tail, capped.
        const N = Math.min(maxTaps, preDelaySamples + Math.ceil(rt60Sec * fs) + 1);
        const impulse = new Float64Array(N);
        if (preDelaySamples < N) impulse[preDelaySamples] = 1; // unit impulse

        // Size scales every delay (0.5x .. 1.5x room); delayScale decorrelates per
        // channel. fs-relative so RT60 holds across sample rates.
        const sizeScale = (0.5 + size) * (fs / 48000) * delayScale;

        // Parallel comb bank -> the dense diffuse body.
        let tail = new Float64Array(N);
        COMB_DELAYS.forEach((base) => {
            const D = Math.max(1, Math.round(base * sizeScale));
            const g = clampGain(rt60ToGain(D, rt60Sec, fs));
            const c = combFilter(impulse, D, g, dampUse);
            for (let n = 0; n < N; n++) tail[n] += c[n] / COMB_DELAYS.length;
        });

        // Series all-passes -> diffusion (smooths the metallic comb ringing).
        const apG = Math.max(0, Math.min(0.95, 0.5 + 0.2 * (diffusion + diffusionBoost)));
        ALLPASS_DELAYS.forEach((base) => {
            tail = allpassFilter(tail, Math.max(1, Math.round(base * sizeScale)), apG);
        });

        if (gainScale !== 1) { for (let n = 0; n < N; n++) tail[n] *= gainScale; }
        return tail;
    };

    // -----------------------------------------------------------------------
    // Multichannel reverb — decorrelated IRs for Stereo / 5.1.
    // Each channel gets a distinct delay scale + pre-delay offset (decorrelation)
    // and role-appropriate diffusion/gain (C anchored & drier, LFE heavily damped,
    // surrounds later & more diffuse).
    // -----------------------------------------------------------------------
    const CHANNEL_LAYOUTS = {
        mono:    ['M'],
        stereo:  ['L', 'R'],
        '5.1':   ['L', 'R', 'C', 'LFE', 'Ls', 'Rs'],
    };

    const channelProfile = (ch) => {
        switch (ch) {
            case 'M':   return { delayScale: 1.000, extraPreMs: 0.0, diffusionBoost:  0.0, gainScale: 1.0 };
            case 'L':   return { delayScale: 0.985, extraPreMs: 0.0, diffusionBoost:  0.0, gainScale: 1.0 };
            case 'R':   return { delayScale: 1.015, extraPreMs: 0.7, diffusionBoost:  0.0, gainScale: 1.0 };
            case 'C':   return { delayScale: 1.000, extraPreMs: 0.0, diffusionBoost: -0.2, gainScale: 0.8 }; // anchored / drier
            case 'LFE': return { delayScale: 1.000, extraPreMs: 0.0, diffusionBoost:  0.0, gainScale: 0.4, dampingBoost: 0.5 }; // heavily damped low tail
            case 'Ls':  return { delayScale: 1.030, extraPreMs: 5.0, diffusionBoost:  0.2, gainScale: 0.9 }; // later + more diffuse
            case 'Rs':  return { delayScale: 1.045, extraPreMs: 6.5, diffusionBoost:  0.2, gainScale: 0.9 };
            default:    return { delayScale: 1.000, extraPreMs: 0.0, diffusionBoost:  0.0, gainScale: 1.0 };
        }
    };

    // Returns { layout, channels:[names], data:{ name: Float64Array } }.
    const synthesizeIRMulti = (params, fs, maxTaps, layoutName) => {
        const chans = CHANNEL_LAYOUTS[layoutName] || CHANNEL_LAYOUTS.mono;
        const data = {};
        chans.forEach((ch) => { data[ch] = synthesizeIR(params, fs, maxTaps, channelProfile(ch)); });
        return { layout: layoutName, channels: chans, data };
    };

    // Schroeder backward-integrated energy decay curve (dB), the smooth RT60 line:
    //   EDC[n] = 10*log10( sum_{k>=n} ir[k]^2 / sum_k ir[k]^2 )
    const energyDecayCurve = (ir) => {
        const edc = new Float64Array(ir.length);
        let running = 0;
        for (let n = ir.length - 1; n >= 0; n--) { running += ir[n] * ir[n]; edc[n] = running; }
        const total = edc[0] || 1e-12;
        for (let n = 0; n < ir.length; n++) edc[n] = 10 * Math.log10(Math.max(edc[n] / total, 1e-12));
        return edc;
    };

    // Peak-preserving decimation to ~targetPoints buckets. Returns an array of
    // {i, v} where i is the original sample index and v is the peak-abs value in
    // that bucket (signed). Keeps the visual envelope honest on long IRs.
    const decimate = (arr, targetPoints) => {
        const n = arr.length;
        if (n <= targetPoints) {
            const out = new Array(n);
            for (let i = 0; i < n; i++) out[i] = { i, v: arr[i] };
            return out;
        }
        const bucket = n / targetPoints;
        const out = [];
        for (let b = 0; b < targetPoints; b++) {
            const start = Math.floor(b * bucket);
            const end = Math.min(n, Math.floor((b + 1) * bucket));
            let peak = 0, peakIdx = start;
            for (let i = start; i < end; i++) {
                if (Math.abs(arr[i]) > Math.abs(peak)) { peak = arr[i]; peakIdx = i; }
            }
            out.push({ i: peakIdx, v: peak });
        }
        return out;
    };

    function clamp01(v, dflt) {
        const x = (v === undefined || v === null || isNaN(v)) ? dflt : v;
        return Math.max(0, Math.min(1, x));
    }

    // -----------------------------------------------------------------------
    // Publish
    // -----------------------------------------------------------------------
    window.OaDsp = {
        _fft,
        _besselI0,
        _windowVal,
        _downloadText,
        rt60ToGain,
        clampGain,
        combFilter,
        allpassFilter,
        synthesizeIR,
        synthesizeIRMulti,
        channelProfile,
        energyDecayCurve,
        decimate,
        COMB_DELAYS,
        ALLPASS_DELAYS,
        CHANNEL_LAYOUTS,
    };
})();
