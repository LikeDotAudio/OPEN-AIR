/**
 * Header: DrumKit.js
 * Purpose: Shared 16-voice drum kit for the Sampler + Sequencer.
 * Description: Single source of truth for the drum-sound names/voices so the
 *   Sampler pads and the Sequencer tracks are the SAME kit. Also provides a
 *   shared AudioContext and a shared sample store, so a sample loaded on a
 *   Sampler pad is played by the Sequencer for that track too.
 *
 * Plain JS (not JSX) so it runs before the text/babel component scripts and
 * window.OA_DRUM_KIT is ready when they execute.
 *
 * Version: 26.07.11.1
 */

// 16 voices: name + synth pitch (Hz) + oscillator type (used when no sample loaded).
// Pad index (0-15) === Sequencer track index === key into OA_DRUM_SAMPLES.
window.OA_DRUM_KIT = [
    { name: 'Kick',    freq: 60,   type: 'sine' },
    { name: 'Snare',   freq: 200,  type: 'sine' },
    { name: 'Hi-Hat',  freq: 800,  type: 'square' },
    { name: 'Perc',    freq: 400,  type: 'sine' },
    { name: 'Clap',    freq: 300,  type: 'square' },
    { name: 'Rim',     freq: 1000, type: 'square' },
    { name: 'Tom Lo',  freq: 100,  type: 'sine' },
    { name: 'Tom Mid', freq: 150,  type: 'sine' },
    { name: 'Tom Hi',  freq: 250,  type: 'sine' },
    { name: 'Cymbal',  freq: 1200, type: 'square' },
    { name: 'Ride',    freq: 900,  type: 'square' },
    { name: 'Cowbell', freq: 540,  type: 'square' },
    { name: 'Conga',   freq: 350,  type: 'sine' },
    { name: 'Clave',   freq: 1100, type: 'sine' },
    { name: 'Shaker',  freq: 1500, type: 'square' },
    { name: 'FX',      freq: 700,  type: 'sawtooth' },
];

// Shared AudioContext so buffers decoded by the Sampler play in the Sequencer.
window.oaAudioCtx = function () {
    if (!window.OA_AUDIO_CTX) {
        window.OA_AUDIO_CTX = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (window.OA_AUDIO_CTX.state === 'suspended') {
        // Best-effort resume (browsers gate audio until a user gesture).
        try { window.OA_AUDIO_CTX.resume(); } catch (e) {}
    }
    return window.OA_AUDIO_CTX;
};

// index -> sample ENTRY { buffer, pitch, loop, fade, name }. Populated by the
// Sampler / AudioEditor, read by both the Sampler pads and the Sequencer.
window.OA_DRUM_SAMPLES = window.OA_DRUM_SAMPLES || {};
// index -> currently-playing looping BufferSource (for auto-loop toggle pads).
window.OA_DRUM_LOOPS = window.OA_DRUM_LOOPS || {};
// Every currently-sounding BufferSource, for live MIDI pitch-bend. OA_PITCH_BEND
// is the current wheel offset in CENTS (±200 = ±2 semitones); it is applied via
// each source's `detune` AudioParam so the sample's base pitch is preserved.
window.OA_DRUM_VOICES = window.OA_DRUM_VOICES || [];
window.OA_PITCH_BEND = window.OA_PITCH_BEND || 0;

// Pre-rendered pitched buffers for Tone Mode (avoids real-time resampling latency)
// rootIdx -> { semitones -> AudioBuffer }
window.OA_TONE_CACHE = window.OA_TONE_CACHE || {};

// Set the global pitch-bend (cents) and retune every sounding voice live.
window.oaSetPitchBend = function (cents) {
    window.OA_PITCH_BEND = cents || 0;
    for (let i = 0; i < window.OA_DRUM_VOICES.length; i++) {
        const s = window.OA_DRUM_VOICES[i];
        try { if (s.detune) s.detune.value = window.OA_PITCH_BEND; } catch (e) {}
    }
};

// Store/replace a pad's sample. opts: { loop, pitch, fade, name }.
window.oaSetDrumSample = function (idx, buffer, opts) {
    opts = opts || {};
    let sampleRoot = null;
    const name = opts.name || '';
    const m = /ROOT-(\d+)/i.exec(name);
    if (m) sampleRoot = parseInt(m[1], 10);
    
    const entry = {
        buffer: buffer,
        pitch: opts.pitch || 1,     // playbackRate multiplier (pitch + speed)
        sampleRoot: sampleRoot,     // MIDI note root parsed from filename
        offset: opts.offset || 0,   // start offset in seconds (time shift)
        end: (opts.end != null ? opts.end : null),   // cut-off in seconds (null = EOF)
        loop: !!opts.loop,
        fade: !!opts.fade,
        name: name,
        folder: opts.folder || '',  // source folder (for set snapshots / revert)
    };
    window.OA_DRUM_SAMPLES[idx] = entry;
    if (window.oaPrecachePad) window.oaPrecachePad(entry);
};

// Patch an existing pad's options (pitch/loop/fade) without re-decoding.
window.oaUpdateDrumSample = function (idx, patch) {
    const e = window.OA_DRUM_SAMPLES[idx];
    if (e) {
        const oldPitch = e.pitch || 1;
        Object.assign(e, patch || {});
        if (e.pitch !== oldPitch || !e.cachedBuffer) {
            if (window.oaPrecachePad) window.oaPrecachePad(e);
        }
    }
};

// Synthesize a kit voice at `time` with `volume` (0..1). Used when no sample.
window.oaPlayDrumVoice = function (ctx, track, time, volume, pan) {
    if (!track) return;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.frequency.value = track.freq;
    osc.type = track.type;
    osc.connect(gain);
    if (pan && ctx.createStereoPanner) { const p = ctx.createStereoPanner(); p.pan.value = Math.max(-1, Math.min(1, pan)); gain.connect(p); p.connect(ctx.destination); }
    else gain.connect(ctx.destination);
    gain.gain.setValueAtTime(Math.max(0.0001, volume), time);
    gain.gain.exponentialRampToValueAtTime(0.001, time + 0.15);
    osc.start(time);
    osc.stop(time + 0.15);
};

// Play a loaded sample ENTRY at `time` with `volume` (0..1); honours pitch,
// loop and fade. Returns the BufferSource so a looping voice can be stopped.
window.oaPlayDrumSample = function (ctx, entry, time, volume, pan) {
    if (!entry || !entry.buffer) return null;
    const src = ctx.createBufferSource();
    const gain = ctx.createGain();
    
    const pitch = entry.pitch || 1;
    const useCache = !!entry.cachedBuffer;
    
    src.buffer = entry.cachedBuffer || entry.buffer;
    src.playbackRate.value = useCache ? 1 : pitch;
    src.loop = !!entry.loop;
    
    const origDur = entry.buffer.duration;
    let offset = Math.max(0, Math.min(entry.offset || 0, origDur - 0.001));
    let end = (entry.end != null && entry.end > offset) ? Math.min(entry.end, origDur) : origDur;
    let region = Math.max(0.001, end - offset);
    
    const playDur = region / pitch;
    
    if (useCache) {
        offset = offset / pitch;
        end = end / pitch;
        region = region / pitch;
    }
    
    if (src.loop) { src.loopStart = offset; src.loopEnd = end; }
    src.connect(gain);
    if (pan && ctx.createStereoPanner) { const p = ctx.createStereoPanner(); p.pan.value = Math.max(-1, Math.min(1, pan)); gain.connect(p); p.connect(ctx.destination); }
    else gain.connect(ctx.destination);
    
    const v = Math.max(0.0001, volume);
    if (entry.fade) {
        const f = Math.min(0.05, playDur * 0.2);
        gain.gain.setValueAtTime(0.0001, time);
        gain.gain.exponentialRampToValueAtTime(v, time + f);
        if (!src.loop) {
            gain.gain.setValueAtTime(v, Math.max(time + f, time + playDur - f));
            gain.gain.exponentialRampToValueAtTime(0.0001, time + playDur);
        }
    } else {
        gain.gain.setValueAtTime(v, time);
    }
    
    if (src.loop) src.start(time, offset);
    else src.start(time, offset, region);
    
    // Register as an active voice so a MIDI pitch-bend can retune it live, and
    // start it at the current wheel offset. Auto-removed when the note ends.
    try {
        if (src.detune) src.detune.value = window.OA_PITCH_BEND || 0;
        window.OA_DRUM_VOICES.push(src);
        src.addEventListener('ended', function () {
            const i = window.OA_DRUM_VOICES.indexOf(src);
            if (i >= 0) window.OA_DRUM_VOICES.splice(i, 1);
        });
    } catch (e) {}
    return src;
};

// Trigger drum voice `idx`: sample (pitch/loop/fade) if loaded, else synth.
// For an auto-loop pad, TOGGLES the loop. Returns true if a loop just STARTED.
window.oaTriggerDrum = function (idx, volume, time) {
    const ctx = window.oaAudioCtx();
    const t = (typeof time === 'number') ? time : ctx.currentTime;
    const vol = Math.max(0, Math.min(1, volume == null ? 1 : volume));
    const entry = window.OA_DRUM_SAMPLES[idx];
    if (entry && entry.buffer) {
        if (entry.loop) {
            const existing = window.OA_DRUM_LOOPS[idx];
            if (existing) { try { existing.stop(); } catch (e) {} window.OA_DRUM_LOOPS[idx] = null; return false; }
            const src = window.oaPlayDrumSample(ctx, entry, t, vol);
            window.OA_DRUM_LOOPS[idx] = src;
            if (src) src.onended = () => { if (window.OA_DRUM_LOOPS[idx] === src) window.OA_DRUM_LOOPS[idx] = null; };
            return true;
        }
        window.oaPlayDrumSample(ctx, entry, t, vol);
        return false;
    }
    window.oaPlayDrumVoice(ctx, window.OA_DRUM_KIT[idx], t, vol);
    return false;
};

// Trigger a drum voice pitched by N semitones (Tone Mode)
window.oaTriggerTone = function(rootIdx, semitones, volume, time) {
    const ctx = window.oaAudioCtx();
    const t = (typeof time === 'number') ? time : ctx.currentTime;
    const vol = Math.max(0, Math.min(1, volume == null ? 1 : volume));
    const entry = window.OA_DRUM_SAMPLES[rootIdx];
    
    if (entry && entry.buffer) {
        const pitchRatio = Math.pow(2, semitones / 12);
        const totalPitch = (entry.pitch || 1) * pitchRatio;
        
        // If we have a pre-rendered cache for this exact pitch, use it at 1x speed to save latency
        const cache = window.OA_TONE_CACHE[rootIdx];
        if (cache && cache[semitones]) {
            window.oaPlayDrumSample(ctx, Object.assign({}, entry, { cachedBuffer: cache[semitones], pitch: totalPitch }), t, vol);
            return true;
        }
        
        // Fallback to real-time resampling if not in cache
        window.oaPlayDrumSample(ctx, Object.assign({}, entry, { pitch: totalPitch }), t, vol);
        return true;
    }
    
    // Fallback to pitched synth voice
    const pitchRatio = Math.pow(2, semitones / 12);
    const track = window.OA_DRUM_KIT[rootIdx];
    if (track) {
        window.oaPlayDrumVoice(ctx, Object.assign({}, track, { freq: track.freq * pitchRatio }), t, vol);
        return true;
    }
    return false;
};

// Pre-render a sample at multiple pitches to eliminate real-time resampling latency
window.oaPrecacheTones = async function(rootIdx) {
    const entry = window.OA_DRUM_SAMPLES[rootIdx];
    if (!entry || !entry.buffer) return;
    
    const origBuf = entry.buffer;
    const basePitch = entry.pitch || 1;
    const OfflineCtx = window.OfflineAudioContext || window.webkitOfflineAudioContext;
    if (!OfflineCtx) return;
    
    window.OA_TONE_CACHE[rootIdx] = window.OA_TONE_CACHE[rootIdx] || {};
    
    // Pre-render 2 octaves down and 3 octaves up
    for (let semitones = -24; semitones <= 36; semitones++) {
        if (window.OA_TONE_CACHE[rootIdx][semitones]) continue; // already cached
        
        try {
            const pitchRatio = Math.pow(2, semitones / 12);
            const totalPitch = basePitch * pitchRatio;
            
            if (totalPitch === 1) {
                window.OA_TONE_CACHE[rootIdx][semitones] = origBuf;
                continue;
            }
            
            const dur = origBuf.duration / totalPitch;
            const offCtx = new OfflineCtx(origBuf.numberOfChannels, Math.ceil(dur * origBuf.sampleRate), origBuf.sampleRate);
            
            const src = offCtx.createBufferSource();
            src.buffer = origBuf;
            src.playbackRate.value = totalPitch;
            src.connect(offCtx.destination);
            src.start(0);
            
            const rendered = await offCtx.startRendering();
            window.OA_TONE_CACHE[rootIdx][semitones] = rendered;
        } catch(e) {
            console.error('Failed to pre-render pitch', semitones, e);
        }
    }
};

// Pre-cache an individual pad's configured pitch to eliminate real-time latency
window.oaPrecachePad = async function(entry) {
    if (!entry || !entry.buffer) return;
    const pitch = entry.pitch || 1;
    if (pitch === 1) {
        entry.cachedBuffer = entry.buffer;
        return;
    }
    const OfflineCtx = window.OfflineAudioContext || window.webkitOfflineAudioContext;
    if (!OfflineCtx) {
        entry.cachedBuffer = entry.buffer;
        return;
    }
    try {
        const dur = entry.buffer.duration / pitch;
        const offCtx = new OfflineCtx(entry.buffer.numberOfChannels, Math.ceil(dur * entry.buffer.sampleRate), entry.buffer.sampleRate);
        const src = offCtx.createBufferSource();
        src.buffer = entry.buffer;
        src.playbackRate.value = pitch;
        src.connect(offCtx.destination);
        src.start(0);
        entry.cachedBuffer = await offCtx.startRendering();
    } catch (e) {
        entry.cachedBuffer = entry.buffer;
    }
};

// ---- Audio decode (with an AIFF/AIFC fallback) ------------------------------
// Chromium's decodeAudioData frequently can't decode AIFF, so parse it by hand.
// Reads an 80-bit IEEE extended float (AIFF sample rate).
function oaRead80(dv, off) {
    const expon = dv.getUint16(off, false);
    const hi = dv.getUint32(off + 2, false);
    const lo = dv.getUint32(off + 6, false);
    const sign = (expon & 0x8000) ? -1 : 1;
    const e = expon & 0x7fff;
    if (e === 0 && hi === 0 && lo === 0) return 0;
    const mant = hi * Math.pow(2, 32) + lo;
    return sign * mant * Math.pow(2, e - 16383 - 63);
}

function oaDecodeAiff(ctx, ab) {
    const dv = new DataView(ab);
    const readStr = (o, n) => { let s = ''; for (let i = 0; i < n; i++) s += String.fromCharCode(dv.getUint8(o + i)); return s; };
    let numChannels = 0, numFrames = 0, bitDepth = 0, sampleRate = 0, compression = 'NONE';
    let ssndDataOffset = 0, ssndSize = 0;
    let off = 12; // skip FORM + size + formType
    while (off + 8 <= ab.byteLength) {
        const id = readStr(off, 4);
        const size = dv.getUint32(off + 4, false);
        const body = off + 8;
        if (id === 'COMM') {
            numChannels = dv.getInt16(body, false);
            numFrames = dv.getUint32(body + 2, false);
            bitDepth = dv.getInt16(body + 6, false);
            sampleRate = oaRead80(dv, body + 8);
            if (size >= 22) compression = readStr(body + 18, 4);
        } else if (id === 'SSND') {
            const dataOffset = dv.getUint32(body, false);
            ssndDataOffset = body + 8 + dataOffset;
            ssndSize = size - 8 - dataOffset;
        }
        off = body + size + (size & 1); // chunks are padded to even length
    }
    if (!numChannels || !sampleRate) throw new Error('unsupported AIFF');
    const le = (compression === 'sowt');   // sowt = byte-swapped (little-endian)
    const bytesPer = bitDepth / 8;
    const frames = numFrames || Math.floor(ssndSize / (bytesPer * numChannels));
    const out = ctx.createBuffer(numChannels, frames, sampleRate);
    const chans = [];
    for (let c = 0; c < numChannels; c++) chans.push(out.getChannelData(c));
    let p = ssndDataOffset;
    for (let f = 0; f < frames; f++) {
        for (let c = 0; c < numChannels; c++) {
            let v = 0;
            if (bitDepth === 16) { v = dv.getInt16(p, le) / 32768; p += 2; }
            else if (bitDepth === 8) { v = dv.getInt8(p) / 128; p += 1; }
            else if (bitDepth === 24) {
                const a0 = dv.getUint8(p), a1 = dv.getUint8(p + 1), a2 = dv.getUint8(p + 2);
                let val = le ? (a0 | (a1 << 8) | (a2 << 16)) : ((a0 << 16) | (a1 << 8) | a2);
                if (val & 0x800000) val -= 0x1000000;
                v = val / 8388608; p += 3;
            } else if (bitDepth === 32) { v = dv.getInt32(p, le) / 2147483648; p += 4; }
            else { p += bytesPer; }
            chans[c][f] = v;
        }
    }
    return out;
}

// Decode any audio ArrayBuffer. AIFF/AIFC is parsed manually (Chromium can't);
// everything else goes to the browser's decodeAudioData.
window.oaDecodeAudio = async function (ctx, arrayBuffer) {
    const b = new Uint8Array(arrayBuffer);
    const tag = (o) => (b.length > o + 3 ? String.fromCharCode(b[o], b[o + 1], b[o + 2], b[o + 3]) : '');
    if (tag(0) === 'FORM' && (tag(8) === 'AIFF' || tag(8) === 'AIFC')) {
        try { return oaDecodeAiff(ctx, arrayBuffer); }
        catch (e) { /* fall through to native (Safari can do AIFF) */ }
    }
    return await ctx.decodeAudioData(arrayBuffer);
};

// ---- Sample persistence (revert samples on reload) --------------------------
// A tiny IndexedDB kv-store to keep the last-picked directory handle (File
// System Access handles are structured-cloneable), so samples can be re-loaded
// next session from their MQTT-stored {name, folder}.
window.oaIdbSet = function (key, val) {
    return new Promise((resolve, reject) => {
        const r = indexedDB.open('oaSound', 1);
        r.onupgradeneeded = () => { r.result.createObjectStore('kv'); };
        r.onsuccess = () => { const tx = r.result.transaction('kv', 'readwrite'); tx.objectStore('kv').put(val, key); tx.oncomplete = () => resolve(); tx.onerror = () => reject(tx.error); };
        r.onerror = () => reject(r.error);
    });
};
window.oaIdbGet = function (key) {
    return new Promise((resolve) => {
        const r = indexedDB.open('oaSound', 1);
        r.onupgradeneeded = () => { r.result.createObjectStore('kv'); };
        r.onsuccess = () => { const tx = r.result.transaction('kv', 'readonly'); const g = tx.objectStore('kv').get(key); g.onsuccess = () => resolve(g.result); g.onerror = () => resolve(null); };
        r.onerror = () => resolve(null);
    });
};

// Walk a persisted root directory handle to a file. folderPath's first segment
// is the root's own name (skipped); the rest are sub-folders.
async function oaNavigateToFile(root, folderPath, name) {
    const parts = (folderPath || '').split('/').filter(Boolean);
    let dir = root;
    for (let i = 1; i < parts.length; i++) dir = await dir.getDirectoryHandle(parts[i]);
    return await dir.getFileHandle(name);
}

// Re-load samples from the persisted folder using per-pad {name, folder} meta.
// MUST be called from a user gesture — may prompt for folder read permission.
window.oaRestoreKit = async function (metaByIdx) {
    const root = await window.oaIdbGet('oaRootDir');
    if (!root) return { ok: false, reason: 'no-folder', restored: 0 };
    if (root.queryPermission) {
        let p = await root.queryPermission({ mode: 'read' });
        if (p !== 'granted' && root.requestPermission) p = await root.requestPermission({ mode: 'read' });
        if (p !== 'granted') return { ok: false, reason: 'permission', restored: 0 };
    }
    let restored = 0;
    for (const idx in metaByIdx) {
        const m = metaByIdx[idx]; if (!m || !m.name) continue;
        try {
            const fh = await oaNavigateToFile(root, m.folder, m.name);
            const file = await fh.getFile();
            const buf = await window.oaDecodeAudio(window.oaAudioCtx(), await file.arrayBuffer());
            window.oaSetDrumSample(Number(idx), buf, { name: m.name });
            restored++;
        } catch (e) { /* file moved/renamed — skip */ }
    }
    return { ok: true, restored };
};

// Ensure read permission on the persisted root folder (call from a user gesture).
window.oaEnsureRootPermission = async function () {
    const root = window.OA_SOUND_DIR || await window.oaIdbGet('oaRootDir');
    if (!root) return false;
    if (root.queryPermission) {
        let p = await root.queryPermission({ mode: 'read' });
        if (p !== 'granted' && root.requestPermission) p = await root.requestPermission({ mode: 'read' });
        if (p !== 'granted') return false;
    }
    window.OA_SOUND_DIR = root;
    return true;
};

// Resolve a File from {folder, name} using the persisted root (if permitted).
window.oaResolveFile = async function (folderPath, name) {
    const root = window.OA_SOUND_DIR || await window.oaIdbGet('oaRootDir');
    if (!root) return null;
    if (root.queryPermission) { const p = await root.queryPermission({ mode: 'read' }); if (p !== 'granted') return null; }
    try { const fh = await oaNavigateToFile(root, folderPath, name); return await fh.getFile(); } catch (e) { return null; }
};

// Encode an AudioBuffer to a 16-bit PCM WAV ArrayBuffer (for RENDER/export).
window.oaEncodeWav = function (audioBuffer) {
    const numCh = audioBuffer.numberOfChannels;
    const len = audioBuffer.length;
    const rate = audioBuffer.sampleRate;
    const blockAlign = numCh * 2;
    const dataSize = len * blockAlign;
    const buffer = new ArrayBuffer(44 + dataSize);
    const dv = new DataView(buffer);
    const writeStr = (o, s) => { for (let i = 0; i < s.length; i++) dv.setUint8(o + i, s.charCodeAt(i)); };
    writeStr(0, 'RIFF'); dv.setUint32(4, 36 + dataSize, true); writeStr(8, 'WAVE');
    writeStr(12, 'fmt '); dv.setUint32(16, 16, true); dv.setUint16(20, 1, true); dv.setUint16(22, numCh, true);
    dv.setUint32(24, rate, true); dv.setUint32(28, rate * blockAlign, true); dv.setUint16(32, blockAlign, true); dv.setUint16(34, 16, true);
    writeStr(36, 'data'); dv.setUint32(40, dataSize, true);
    const chans = [];
    for (let c = 0; c < numCh; c++) chans.push(audioBuffer.getChannelData(c));
    let off = 44;
    for (let i = 0; i < len; i++) {
        for (let c = 0; c < numCh; c++) {
            const s = Math.max(-1, Math.min(1, chans[c][i]));
            dv.setInt16(off, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
            off += 2;
        }
    }
    return buffer;
};
