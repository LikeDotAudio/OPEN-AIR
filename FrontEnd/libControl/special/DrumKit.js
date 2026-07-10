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
 * Version: 26.07.10.1
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

// index -> decoded AudioBuffer. Populated by the Sampler on load, read by both.
window.OA_DRUM_SAMPLES = window.OA_DRUM_SAMPLES || {};

// Synthesize a kit voice at `time` with `volume` (0..1). Used when no sample.
window.oaPlayDrumVoice = function (ctx, track, time, volume) {
    if (!track) return;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.frequency.value = track.freq;
    osc.type = track.type;
    osc.connect(gain);
    gain.connect(ctx.destination);
    gain.gain.setValueAtTime(Math.max(0.0001, volume), time);
    gain.gain.exponentialRampToValueAtTime(0.001, time + 0.15);
    osc.start(time);
    osc.stop(time + 0.15);
};

// Play a loaded sample buffer at `time` with `volume` (0..1).
window.oaPlayDrumSample = function (ctx, buffer, time, volume) {
    const src = ctx.createBufferSource();
    const gain = ctx.createGain();
    src.buffer = buffer;
    src.connect(gain);
    gain.connect(ctx.destination);
    gain.gain.setValueAtTime(Math.max(0.0001, volume), time);
    src.start(time);
};

// Trigger drum voice `idx` (0-15): sample if loaded, else synth. `time` optional
// (defaults to now); `volume` 0..1. Central helper both components call.
window.oaTriggerDrum = function (idx, volume, time) {
    const ctx = window.oaAudioCtx();
    const t = (typeof time === 'number') ? time : ctx.currentTime;
    const vol = Math.max(0, Math.min(1, volume == null ? 1 : volume));
    const buf = window.OA_DRUM_SAMPLES[idx];
    if (buf) window.oaPlayDrumSample(ctx, buf, t, vol);
    else window.oaPlayDrumVoice(ctx, window.OA_DRUM_KIT[idx], t, vol);
};
