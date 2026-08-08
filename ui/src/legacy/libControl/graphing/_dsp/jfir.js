/**
 * Header: jfir.js
 * Purpose: JFIR — the OPEN-AIR "JSON FIR" bundle format + builder.
 * Description: A JFIR is a single JSON object that captures everything needed to
 *   reproduce a filter/effect preset: the source **parameters**, the generated
 *   **FIR** impulse response (one tap array per channel — so 5.1 fits in one object),
 *   and the **CSV of the curve**. Used by both the Equalization and Reverb graphs
 *   (and, later, Delay / Flanger / Chorus).
 *
 * Attached to window.OaJfir. Uses window.OaDsp._downloadText for the actual download
 * with a local fallback so a script-load-order regression degrades gracefully.
 *
 * Schema (version 1):
 * {
 *   "format": "JFIR", "version": 1,
 *   "kind": "reverb" | "eq" | ...,
 *   "label": "Master Bus Reverb",
 *   "generator": "OPEN-AIR",
 *   "created": "<ISO-8601 | null>",
 *   "sampleRate": 48000,
 *   "parameters": { ...preset params... },
 *   "fir": {
 *     "taps": 4096, "phase": "minimum", "window": "hann",
 *     "channels": ["L","R","C","LFE","Ls","Rs"],   // order
 *     "data": { "L": [ ...taps... ], "R": [ ... ], ... }
 *   },
 *   "curve": { "columns": ["Freq","Gain"], "csv": "Freq,Gain\n..." } | null
 * }
 *
 * Version: 26.07.06.1
 * Change Log:
 * - 2026-07-06: Initial JFIR builder (Phase 4 of REVERB PLAN.MD).
 */

(function () {
    const FORMAT = "JFIR";
    const VERSION = 1;

    const _now = () => { try { return new Date().toISOString(); } catch (e) { return null; } };

    const _fallbackDownload = (content, filename, mime) => {
        const blob = new Blob([content], { type: mime });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = filename;
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };
    const _download = (content, filename, mime) =>
        ((window.OaDsp && window.OaDsp._downloadText) || _fallbackDownload)(content, filename, mime);

    // Round a tap container (Float64Array or Array) to a text-safe Array of numbers.
    const _taps = (arr, digits) => {
        const d = (digits === undefined) ? 10 : digits;
        const out = new Array(arr.length);
        for (let i = 0; i < arr.length; i++) out[i] = +(+arr[i]).toFixed(d);
        return out;
    };

    // Build a JFIR object from parts.
    //   opts = {
    //     kind, label, sampleRate, parameters, digits,
    //     fir: { taps, phase, window, channels:[names], data:{name: Float64Array|Array} },
    //     curve: { columns:[...], csv:"..." } | null
    //   }
    const build = (opts) => {
        opts = opts || {};
        const firIn = opts.fir || {};
        const channels = firIn.channels || Object.keys(firIn.data || {});
        const data = {};
        channels.forEach((ch) => {
            const src = (firIn.data || {})[ch];
            if (src) data[ch] = _taps(src, opts.digits);
        });
        return {
            format: FORMAT,
            version: VERSION,
            kind: opts.kind || "unknown",
            label: opts.label || "",
            generator: "OPEN-AIR",
            created: _now(),
            sampleRate: opts.sampleRate || 48000,
            parameters: opts.parameters || {},
            fir: {
                taps: firIn.taps || (channels.length ? (data[channels[0]] || []).length : 0),
                phase: firIn.phase || "linear",
                window: firIn.window || "hann",
                channels: channels,
                data: data
            },
            curve: opts.curve || null
        };
    };

    const stringify = (jfir, pretty) => JSON.stringify(jfir, null, pretty === false ? 0 : 2);

    // Sanitize a label into a filename stem.
    const _stem = (label, kind) => {
        const base = (label || kind || "export").toString().trim().toLowerCase()
            .replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
        return base || (kind || "export");
    };

    // Download the JFIR as a .jfir (JSON) file.
    const download = (jfir, filename) => {
        const name = filename || (_stem(jfir.label, jfir.kind) + '.jfir');
        _download(stringify(jfir), name, "application/json;charset=utf-8;");
    };

    // Parse + validate a JFIR blob (string or object).
    const parse = (text) => {
        const obj = (typeof text === 'string') ? JSON.parse(text) : text;
        if (!obj || obj.format !== FORMAT) throw new Error("Not a JFIR object");
        return obj;
    };

    // One channel's taps -> .fir text (one tap per line).
    const firText = (taps, digits) => {
        const d = (digits === undefined) ? 10 : digits;
        let s = '';
        for (let i = 0; i < taps.length; i++) s += (+taps[i]).toFixed(d) + '\n';
        return s;
    };

    // Download each channel of a JFIR as a separate .fir file (the "5 files" option).
    const downloadSeparateFir = (jfir, digits) => {
        const stem = _stem(jfir.label, jfir.kind);
        const chans = (jfir.fir && jfir.fir.channels) || [];
        chans.forEach((ch) => {
            const taps = jfir.fir.data[ch];
            if (!taps) return;
            const suffix = (chans.length === 1) ? '' : ('_' + ch);
            _download(firText(taps, digits), `${stem}${suffix}.fir`, 'text/plain;charset=utf-8;');
        });
    };

    window.OaJfir = {
        FORMAT, VERSION,
        build, stringify, download, parse, firText, downloadSeparateFir,
    };
})();
