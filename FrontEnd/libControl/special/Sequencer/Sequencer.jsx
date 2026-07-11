// The 16-voice drum kit is shared with the Sampler (DrumKit.js) so a Sampler pad
// and the matching Sequencer track are the SAME voice — including any sample
// loaded onto that pad.
const TRACKS = window.OA_DRUM_KIT || [];
const STEP_OPTIONS = [4, 8, 16, 32, 64];   // selectable pattern lengths
const DEFAULT_STEPS = 16;
const LIBRARY_KEY = 'oaSequencerLibrary';

// A step cell holds a VELOCITY: 0 = off, 1-100 = on at that intensity.
// velOf tolerates legacy boolean grids (true -> 100).
const emptyPattern = (steps) => Array(TRACKS.length).fill().map(() => Array(steps).fill(0));
const velOf = (c) => (typeof c === 'number' ? c : (c ? 100 : 0));
const clonePattern = (p) => p.map((row) => [...row]);

const loadLibrary = () => {
    try {
        return JSON.parse(window.localStorage.getItem(LIBRARY_KEY)) || [];
    } catch (e) {
        return [];
    }
};

// Self-contained rotary knob for tempo: drag up/down or scroll to change.
const BpmKnob = ({ value, min = 40, max = 300, onChange, flash }) => {
    const drag = React.useRef(null);
    const angle = -135 + ((value - min) / (max - min)) * 270;   // 270° sweep
    const clamp = (v) => Math.round(Math.max(min, Math.min(max, v)));
    const onDown = (e) => {
        e.preventDefault();
        drag.current = { y: e.clientY, v: value };
        try { e.currentTarget.setPointerCapture(e.pointerId); } catch (x) {}
    };
    const onMove = (e) => {
        if (!drag.current) return;
        onChange(clamp(drag.current.v + (drag.current.y - e.clientY) * 0.5)); // 0.5 BPM/px
    };
    const onUp = (e) => { drag.current = null; try { e.currentTarget.releasePointerCapture(e.pointerId); } catch (x) {} };
    const onWheel = (e) => { e.preventDefault(); onChange(clamp(value - Math.sign(e.deltaY))); };
    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1px' }}>
            <div
                onPointerDown={onDown} onPointerMove={onMove} onPointerUp={onUp} onPointerLeave={onUp} onWheel={onWheel}
                title="Drag up/down or scroll to change BPM"
                style={{ width: '42px', height: '42px', borderRadius: '50%', background: 'radial-gradient(circle at 50% 35%, #444, #1a1a1a)', border: flash ? '2px solid #f4902c' : '2px solid #555', position: 'relative', cursor: 'ns-resize', touchAction: 'none', boxShadow: flash ? '0 0 14px rgba(244,144,44,0.9)' : 'inset 0 2px 5px rgba(0,0,0,0.6)', transition: 'box-shadow 0.08s, border-color 0.08s' }}
            >
                <div style={{ position: 'absolute', inset: 0, transform: `rotate(${angle}deg)` }}>
                    <div style={{ position: 'absolute', left: '50%', top: '4px', width: '3px', height: '13px', background: '#f4902c', transform: 'translateX(-50%)', borderRadius: '2px' }} />
                </div>
            </div>
            <span style={{ fontSize: '11px', color: '#f4902c', fontWeight: 'bold', lineHeight: 1 }}>{value}</span>
            <span style={{ fontSize: '8px', color: '#888', letterSpacing: '0.5px' }}>BPM</span>
        </div>
    );
};

// Small rotary knob (volume / pan). Drag up/down or scroll.
const MiniKnob = ({ value, min, max, label, display, onChange, size = 42 }) => {
    const drag = React.useRef(null);
    const frac = (value - min) / ((max - min) || 1);
    const angle = -135 + frac * 270;
    const clamp = (v) => Math.max(min, Math.min(max, v));
    const onDown = (e) => { e.preventDefault(); drag.current = { y: e.clientY, v: value }; try { e.currentTarget.setPointerCapture(e.pointerId); } catch (x) {} };
    const onMove = (e) => { if (!drag.current) return; onChange(clamp(drag.current.v + (drag.current.y - e.clientY) * (max - min) / 120)); };
    const onUp = () => { drag.current = null; };
    const onWheel = (e) => { e.preventDefault(); onChange(clamp(value + (e.deltaY < 0 ? 1 : -1) * (max - min) / 60)); };
    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px' }}>
            <div onPointerDown={onDown} onPointerMove={onMove} onPointerUp={onUp} onPointerLeave={onUp} onWheel={onWheel}
                style={{ width: size, height: size, borderRadius: '50%', background: 'radial-gradient(circle at 50% 35%, #444, #1a1a1a)', border: '2px solid #555', position: 'relative', cursor: 'ns-resize', touchAction: 'none' }}>
                <div style={{ position: 'absolute', inset: 0, transform: `rotate(${angle}deg)` }}>
                    <div style={{ position: 'absolute', left: '50%', top: '3px', width: '3px', height: `${Math.round(size * 0.3)}px`, background: '#f4902c', transform: 'translateX(-50%)', borderRadius: '2px' }} />
                </div>
            </div>
            <span style={{ fontSize: '10px', color: '#f4902c', fontWeight: 'bold', lineHeight: 1 }}>{display}</span>
            <span style={{ fontSize: '8px', color: '#888' }}>{label}</span>
        </div>
    );
};

// Per-track sample menu: waveform + pitch + time-shift, opened by clicking a
// track name. Edits the shared kit entry (OA_DRUM_SAMPLES[trkIdx]) directly.
const TrackSampleMenu = ({ trkIdx, trackName, anchor, version, onBrowse, onClose, onChange, vol, pan, onVol, onPan }) => {
    const entry = (window.OA_DRUM_SAMPLES && window.OA_DRUM_SAMPLES[trkIdx]) || null;
    const hasBuf = !!(entry && entry.buffer);
    const canvasRef = React.useRef(null);
    const semiFromPitch = (p) => Math.round(12 * Math.log2(p || 1));
    const [pitchSemi, setPitchSemi] = React.useState(semiFromPitch(entry && entry.pitch));
    const [offset, setOffset] = React.useState((entry && entry.offset) || 0);
    const [loop, setLoop] = React.useState(!!(entry && entry.loop));
    const [end, setEnd] = React.useState((entry && entry.end != null) ? entry.end : (entry && entry.buffer ? entry.buffer.duration : 0));

    React.useEffect(() => {
        const e = window.OA_DRUM_SAMPLES[trkIdx];
        setPitchSemi(semiFromPitch(e && e.pitch));
        setOffset((e && e.offset) || 0);
        setLoop(!!(e && e.loop));
        setEnd((e && e.end != null) ? e.end : (e && e.buffer ? e.buffer.duration : 0));
    }, [version]);

    React.useEffect(() => {
        const c = canvasRef.current; if (!c) return;
        c.width = c.clientWidth; c.height = c.clientHeight;
        const cx = c.getContext('2d');
        cx.fillStyle = '#0a0a0a'; cx.fillRect(0, 0, c.width, c.height);
        const e = window.OA_DRUM_SAMPLES[trkIdx];
        if (!e || !e.buffer) return;
        const data = e.buffer.getChannelData(0);
        const step = Math.ceil(data.length / c.width); const amp = c.height / 2;
        cx.strokeStyle = '#f4902c'; cx.beginPath();
        for (let x = 0; x < c.width; x++) { let mn = 1, mx = -1; for (let j = 0; j < step; j++) { const d = data[x * step + j]; if (d === undefined) break; if (d < mn) mn = d; if (d > mx) mx = d; } cx.moveTo(x, (1 + mn) * amp); cx.lineTo(x, (1 + mx) * amp); }
        cx.stroke();
        if (e.buffer.duration) {
            const ox = (e.offset || 0) / e.buffer.duration * c.width; cx.strokeStyle = '#8ab4f8'; cx.beginPath(); cx.moveTo(ox, 0); cx.lineTo(ox, c.height); cx.stroke();
            const endSec = (e.end != null ? e.end : e.buffer.duration);
            const ex = endSec / e.buffer.duration * c.width; cx.strokeStyle = '#e57373'; cx.beginPath(); cx.moveTo(ex, 0); cx.lineTo(ex, c.height); cx.stroke();
        }
    }, [version, offset, end]);

    const applyPitch = (s) => { setPitchSemi(s); window.oaUpdateDrumSample(trkIdx, { pitch: Math.pow(2, s / 12) }); onChange && onChange(); };
    const applyOffset = (o) => { setOffset(o); window.oaUpdateDrumSample(trkIdx, { offset: o }); onChange && onChange(); };
    const applyLoop = (b) => { setLoop(b); window.oaUpdateDrumSample(trkIdx, { loop: b }); onChange && onChange(); };
    const applyEnd = (val) => { setEnd(val); window.oaUpdateDrumSample(trkIdx, { end: val }); onChange && onChange(); };
    const dur = hasBuf ? entry.buffer.duration : 0;

    return (
        <React.Fragment>
            <div onClick={onClose} style={{ position: 'fixed', inset: 0, zIndex: 9999 }} />
            <div style={{ position: 'fixed', zIndex: 10000, width: '300px', top: Math.min(anchor.y, window.innerHeight - 340), left: Math.min(anchor.x, window.innerWidth - 320), background: '#1c1c1c', border: '1px solid #f4902c', borderRadius: '6px', padding: '12px', color: '#eee', boxShadow: '0 8px 30px rgba(0,0,0,0.6)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ color: '#f4902c', fontWeight: 'bold', fontSize: '13px' }}>{trackName}</span>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#888', cursor: 'pointer', fontSize: '16px' }}>×</button>
                </div>
                <div style={{ fontSize: '11px', color: '#aaa', marginBottom: '6px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {hasBuf ? (entry.name || 'sample') : 'Synth voice — no sample loaded'}
                </div>
                <div style={{ width: '100%', height: '56px', background: '#0a0a0a', border: '1px solid #444' }}>
                    <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />
                </div>
                <div style={{ display: 'flex', gap: '8px', marginTop: '8px', alignItems: 'center' }}>
                    <button onClick={onBrowse} style={{ flex: 1, background: '#f4902c', color: '#111', border: 'none', borderRadius: '3px', padding: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '12px' }}>📁 Browse sample…</button>
                    <label title="Loop the sample (Sampler pad hold)" style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: '#ccc', cursor: 'pointer' }}>
                        <input type="checkbox" checked={loop} disabled={!hasBuf} onChange={(e) => applyLoop(e.target.checked)} /> Loop
                    </label>
                    <button onClick={() => window.oaTriggerDrum && window.oaTriggerDrum(trkIdx, 1)} title="Preview" style={{ background: '#333', color: '#fff', border: '1px solid #444', borderRadius: '3px', padding: '6px 12px', cursor: 'pointer', fontSize: '12px' }}>►</button>
                </div>
                <div style={{ marginTop: '10px', opacity: hasBuf ? 1 : 0.4 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#aaa' }}><span>PITCH</span><span style={{ color: '#f4902c' }}>{pitchSemi > 0 ? '+' : ''}{pitchSemi} st</span></div>
                    <input type="range" min="-12" max="12" step="1" value={pitchSemi} disabled={!hasBuf} onChange={(e) => applyPitch(Number(e.target.value))} style={{ width: '100%' }} />
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#aaa', marginTop: '6px' }}><span style={{ color: '#8ab4f8' }}>TIME SHIFT (start)</span><span style={{ color: '#f4902c' }}>{offset.toFixed(3)}s</span></div>
                    <input type="range" min="0" max={dur ? Number((dur * 0.9).toFixed(3)) : 0} step="0.001" value={offset} disabled={!hasBuf} onChange={(e) => applyOffset(Number(e.target.value))} style={{ width: '100%' }} />
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#aaa', marginTop: '6px' }}><span style={{ color: '#e57373' }}>END / CUT-OFF</span><span style={{ color: '#f4902c' }}>{Number(end || 0).toFixed(3)}s{dur && Math.abs((end || 0) - dur) < 0.0005 ? ' (EOF)' : ''}</span></div>
                    <input type="range" min="0.01" max={dur ? Number(dur.toFixed(3)) : 0} step="0.001" value={Math.min(end || 0, dur || 0)} disabled={!hasBuf} onChange={(e) => applyEnd(Math.max(offset + 0.01, Number(e.target.value)))} style={{ width: '100%' }} />
                </div>
                <div style={{ display: 'flex', gap: '20px', justifyContent: 'center', marginTop: '12px', borderTop: '1px solid #333', paddingTop: '10px' }}>
                    <MiniKnob value={Math.round((vol == null ? 1 : vol) * 100)} min={0} max={100} label="VOL" display={`${Math.round((vol == null ? 1 : vol) * 100)}`} onChange={(v) => onVol && onVol(v / 100)} />
                    <MiniKnob value={Math.round((pan || 0) * 100)} min={-100} max={100} label="PAN" display={`${Math.round((pan || 0) * 100)}`} onChange={(v) => onPan && onPan(v / 100)} />
                </div>
            </div>
        </React.Fragment>
    );
};

const Sequencer = ({ label = "Pattern Sequencer" }) => {
    const audioCtxRef = React.useRef(null);
    const [isPlaying, setIsPlaying] = React.useState(false);
    const [currentStep, setCurrentStep] = React.useState(0);

    // MQTT topics for this sequencer instance (retained, so state survives
    // reloads and syncs to any other client viewing the same sequencer).
    const safeLabel = label.replace(/[^A-Za-z0-9]+/g, '_');
    const patternTopic = `OpenAir/Gui/Sequencer/${safeLabel}/pattern`;
    const libraryTopic = `OpenAir/Gui/Sequencer/${safeLabel}/library`;

    // Live sequence (grid + tempo) — pushed to and read from MQTT. Wrapped in an
    // object so useMqttState treats it as a structured payload, not a scalar.
    const [seq, setSeq] = window.useMqttState(patternTopic, { grid: emptyPattern(DEFAULT_STEPS), bpm: 120, steps: DEFAULT_STEPS });
    const steps = (seq && seq.steps) || DEFAULT_STEPS;
    const pattern = (seq && seq.grid) || emptyPattern(steps);
    const bpm = (seq && seq.bpm) || 120;

    // The scheduler runs in a stale RAF closure, so it reads live values via refs.
    // This is what makes a step toggled ON mid-playback sound on its next pass,
    // and a BPM/step change take effect immediately.
    const stepsRef = React.useRef(steps);
    stepsRef.current = steps;
    const patternRef = React.useRef(pattern);
    patternRef.current = pattern;
    const bpmRef = React.useRef(bpm);
    bpmRef.current = bpm;

    const setPattern = (grid) => setSeq({ grid, bpm, steps });
    const setBpm = (nextBpm) => setSeq({ grid: pattern, bpm: nextBpm, steps });

    // Tap tempo — average the last few tap intervals; flashes the knob per tap.
    const tapTimesRef = React.useRef([]);
    const tapFlashRef = React.useRef(null);
    const [tapping, setTapping] = React.useState(false);
    const tapTempo = () => {
        const now = performance.now();
        const times = tapTimesRef.current;
        if (times.length && now - times[times.length - 1] > 2000) times.length = 0; // reset after a pause
        times.push(now);
        if (times.length > 6) times.shift();
        if (times.length >= 2) {
            let sum = 0; for (let i = 1; i < times.length; i++) sum += times[i] - times[i - 1];
            setBpm(Math.max(40, Math.min(300, Math.round(60000 / (sum / (times.length - 1))))));
        }
        setTapping(true);
        if (tapFlashRef.current) clearTimeout(tapFlashRef.current);
        tapFlashRef.current = setTimeout(() => setTapping(false), 130);
    };

    // Change pattern length (4/8/16): truncate or pad each track row to n steps.
    const setSteps = (n) => {
        const grid = pattern.map((row) => {
            const r = row.slice(0, n);
            while (r.length < n) r.push(0);
            return r;
        });
        setSeq({ grid, bpm, steps: n });
    };

    // Per-track mute: silences that track's audio but keeps its pattern intact.
    // Local to this client (each client renders its own audio); read via ref in
    // the scheduler's stale RAF closure.
    const [mutes, setMutes] = React.useState(() => Array(TRACKS.length).fill(false));
    const mutesRef = React.useRef(mutes);
    mutesRef.current = mutes;
    const toggleMute = (trkIdx) =>
        setMutes((prev) => { const n = [...prev]; n[trkIdx] = !n[trkIdx]; return n; });

    // Per-track volume (0-1) + pan (-1..1), local to this client. Read via refs
    // in the scheduler's stale RAF closure.
    const [trackVol, setTrackVol] = React.useState(() => Array(TRACKS.length).fill(1));
    const [trackPan, setTrackPan] = React.useState(() => Array(TRACKS.length).fill(0));
    const trackVolRef = React.useRef(trackVol); trackVolRef.current = trackVol;
    const trackPanRef = React.useRef(trackPan); trackPanRef.current = trackPan;

    // Record mode: while recording AND playing, pad hits from the Sampler write
    // into the current step of the matching track at their played velocity.
    const [recording, setRecording] = React.useState(false);
    const recordingRef = React.useRef(recording); recordingRef.current = recording;
    const playingRef = React.useRef(isPlaying); playingRef.current = isPlaying;
    const setSeqRef = React.useRef(setSeq); setSeqRef.current = setSeq;

    // Write a velocity into one step using the LIVE grid (ref) — safe from the
    // stale render closures the record/drag listeners capture.
    const writeStepVel = (trkIdx, step, vel) => {
        const v = Math.max(0, Math.min(100, Math.round(vel)));
        const grid = patternRef.current.map((r) => r.slice());
        grid[trkIdx][step] = v;
        setSeqRef.current({ grid, bpm: bpmRef.current, steps: stepsRef.current });
    };

    // One-shot preview of a track's voice (never loops) — audible feedback when
    // a step is placed. Also flashes the matching Sampler pad.
    const previewVoice = (trkIdx, vel) => {
        const ctx = window.oaAudioCtx();
        const vol = (vel / 100) * (trackVolRef.current[trkIdx] == null ? 1 : trackVolRef.current[trkIdx]);
        const pan = trackPanRef.current[trkIdx] || 0;
        const entry = window.OA_DRUM_SAMPLES && window.OA_DRUM_SAMPLES[trkIdx];
        if (entry && entry.buffer && window.oaPlayDrumSample) window.oaPlayDrumSample(ctx, Object.assign({}, entry, { loop: false }), ctx.currentTime, vol, pan);
        else if (window.oaPlayDrumVoice) window.oaPlayDrumVoice(ctx, TRACKS[trkIdx], ctx.currentTime, vol, pan);
        window.dispatchEvent(new CustomEvent('oa-drum-play', { detail: { idx: trkIdx, velocity: vel } }));
    };

    React.useEffect(() => {
        const onDrumHit = (e) => {
            if (!recordingRef.current || !playingRef.current) return;
            const idx = e.detail && e.detail.idx;
            if (idx == null || idx < 0 || idx >= TRACKS.length) return;
            const step = currentStepRef.current % stepsRef.current;
            writeStepVel(idx, step, Math.max(1, (e.detail.velocity || 100)));
        };
        window.addEventListener('oa-drum-hit', onDrumHit);
        return () => window.removeEventListener('oa-drum-hit', onDrumHit);
    }, []);

    // Per-track sample menu (click a track name) + its Browse target.
    const [trackMenu, setTrackMenu] = React.useState(null);   // { trkIdx, x, y }
    const [browseTrack, setBrowseTrack] = React.useState(null);
    const [trackVer, setTrackVer] = React.useState(0);
    const trackPublish = window.useMqttPublish ? window.useMqttPublish() : null;
    const loadTrackSample = async (trkIdx, file, meta) => {
        try {
            const ctx = window.oaAudioCtx();
            const buf = await window.oaDecodeAudio(ctx, await file.arrayBuffer());
            const prev = window.OA_DRUM_SAMPLES[trkIdx] || {};
            window.oaSetDrumSample(trkIdx, buf, { name: file.name, pitch: prev.pitch, loop: prev.loop, fade: prev.fade, offset: 0, folder: (meta && meta.folder) || '' });
            setTrackVer((v) => v + 1);
            if (trackPublish) trackPublish(`OpenAir/Gui/DrumKit/${trkIdx}/sample`, { name: file.name, folder: (meta && meta.folder) || '' });
        } catch (e) { console.error('🛑 [Sequencer] load track sample:', e); }
    };

    // Saved-pattern library — also pushed to / read from MQTT (retained), with a
    // localStorage seed so it still loads when the broker is offline.
    const [lib, setLib] = window.useMqttState(libraryTopic, { items: loadLibrary() });
    const library = (lib && lib.items) || [];
    const setLibraryItems = (items) => setLib({ items });
    React.useEffect(() => {
        if (lib && lib.items) {
            try {
                window.localStorage.setItem(LIBRARY_KEY, JSON.stringify(lib.items));
            } catch (e) { /* storage full / unavailable — keep running */ }
        }
    }, [lib]);
    
    // Lookahead scheduling state
    const nextNoteTimeRef = React.useRef(0);
    const currentStepRef = React.useRef(0);
    const timerIDRef = React.useRef(null);
    const lookahead = 25.0; // ms
    const scheduleAheadTime = 0.1; // s

    const getAudioCtx = () => {
        if (!audioCtxRef.current) {
            // Use the SHARED context so buffers the Sampler decoded play here too.
            audioCtxRef.current = window.oaAudioCtx
                ? window.oaAudioCtx()
                : new (window.AudioContext || window.webkitAudioContext)();
        }
        return audioCtxRef.current;
    };

    const nextNote = () => {
        const secondsPerBeat = 60.0 / bpmRef.current;
        nextNoteTimeRef.current += 0.25 * secondsPerBeat; // 16th note
        currentStepRef.current = (currentStepRef.current + 1) % stepsRef.current;
    };

    const scheduleNote = (stepNumber, time) => {
        // Only update UI if we're roughly at that time (sync UI to audio)
        requestAnimationFrame(() => setCurrentStep(stepNumber));
        
        const ctx = getAudioCtx();
        // Here we'd normally trigger sounds from the Sampler state.
        // For this demo, we'll synthesize simple beeps based on active tracks.
        patternRef.current.forEach((track, trkIdx) => {
            const vel = velOf(track[stepNumber]);
            if (vel > 0 && !mutesRef.current[trkIdx]) {
                const vol = (vel / 100) * (trackVolRef.current[trkIdx] == null ? 1 : trackVolRef.current[trkIdx]);
                const pan = trackPanRef.current[trkIdx] || 0;
                // Flash the matching Sampler pad's glow at this intensity, timed
                // to when the note actually sounds (the scheduler runs ahead).
                const glowDelay = Math.max(0, (time - ctx.currentTime) * 1000);
                setTimeout(() => window.dispatchEvent(new CustomEvent('oa-drum-play', { detail: { idx: trkIdx, velocity: vel } })), glowDelay);
                // Play the shared voice: the Sampler's loaded sample for this
                // track if present (with its pitch/fade), otherwise the synth voice.
                const entry = window.OA_DRUM_SAMPLES && window.OA_DRUM_SAMPLES[trkIdx];
                if (entry && entry.buffer && window.oaPlayDrumSample) {
                    // One-shot per step (never loop in the sequence), but keep cut-off/pitch/fade.
                    window.oaPlayDrumSample(ctx, Object.assign({}, entry, { loop: false }), time, vol, pan);
                } else if (window.oaPlayDrumVoice) {
                    window.oaPlayDrumVoice(ctx, TRACKS[trkIdx], time, vol, pan);
                } else {
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.frequency.value = TRACKS[trkIdx].freq;
                    osc.type = TRACKS[trkIdx].type;
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    gain.gain.setValueAtTime(vol, time);
                    gain.gain.exponentialRampToValueAtTime(0.001, time + 0.1);
                    osc.start(time);
                    osc.stop(time + 0.1);
                }
            }
        });
    };

    const scheduler = () => {
        const ctx = getAudioCtx();
        // While there are notes that will need to play before the next interval, schedule them
        while (nextNoteTimeRef.current < ctx.currentTime + scheduleAheadTime) {
            scheduleNote(currentStepRef.current, nextNoteTimeRef.current);
            nextNote();
        }
        timerIDRef.current = requestAnimationFrame(scheduler);
    };

    const togglePlayback = () => {
        const ctx = getAudioCtx();
        if (isPlaying) {
            cancelAnimationFrame(timerIDRef.current);
            setIsPlaying(false);
            setCurrentStep(0);
        } else {
            // Un-suspend AudioContext on first play if needed (browser policy)
            if (ctx.state === 'suspended') ctx.resume();
            
            setIsPlaying(true);
            currentStepRef.current = 0;
            nextNoteTimeRef.current = ctx.currentTime + 0.05; // start shortly
            scheduler();
        }
    };

    // Click a step = toggle on(100)/off. Click-and-HOLD (or drag) = it becomes a
    // small vertical fader; drag up/down to set that step's intensity (velocity).
    const [activeFader, setActiveFader] = React.useState(null); // { trkIdx, step, vel }

    const onStepPointerDown = (e, trkIdx, step) => {
        e.preventDefault();
        // Plain click = toggle. Click-drag = PAINT the row with that on/off value.
        // ALT+drag = large, detailed intensity fader.
        if (!e.altKey) {
            const paintVel = velOf(patternRef.current[trkIdx][step]) > 0 ? 0 : 100;
            writeStepVel(trkIdx, step, paintVel);
            if (paintVel > 0) previewVoice(trkIdx, paintVel);   // sound when placed
            const painted = new Set([step]);
            const move = (ev) => {
                const el = document.elementFromPoint(ev.clientX, ev.clientY);
                if (el && el.dataset && el.dataset.oaTrk !== undefined && Number(el.dataset.oaTrk) === trkIdx) {
                    const s = Number(el.dataset.oaStep);
                    if (!painted.has(s)) { painted.add(s); writeStepVel(trkIdx, s, paintVel); if (paintVel > 0) previewVoice(trkIdx, paintVel); }
                }
            };
            const up = () => { window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', up); };
            window.addEventListener('pointermove', move);
            window.addEventListener('pointerup', up);
            return;
        }
        const startY = e.clientY;
        const startVel = velOf(patternRef.current[trkIdx][step]) || 100;
        writeStepVel(trkIdx, step, startVel);                 // ensure the step is on
        setActiveFader({ trkIdx, step, vel: Math.round(startVel), x: e.clientX, y: e.clientY });
        const move = (ev) => {
            // Fine control: ~0.5 velocity per pixel (full range spans ~200px).
            const vel = Math.max(1, Math.min(100, startVel + (startY - ev.clientY) * 0.5));
            writeStepVel(trkIdx, step, vel);
            setActiveFader((f) => (f ? { ...f, vel: Math.round(vel) } : f));
        };
        const up = () => {
            window.removeEventListener('pointermove', move);
            window.removeEventListener('pointerup', up);
            setActiveFader(null);
        };
        window.addEventListener('pointermove', move);
        window.addEventListener('pointerup', up);
    };

    const savePattern = () => {
        const name = (window.prompt('Save pattern as:', `Pattern ${library.length + 1}`) || '').trim();
        if (!name) return;
        const entry = { name, bpm, steps, data: clonePattern(pattern) };
        // Overwrite an existing entry with the same name, otherwise append
        const idx = library.findIndex((p) => p.name === name);
        let next;
        if (idx === -1) {
            next = [...library, entry];
        } else {
            next = [...library];
            next[idx] = entry;
        }
        setLibraryItems(next);
    };

    const loadPattern = (entry) => {
        const loadedSteps = (entry.data[0] && entry.data[0].length) || entry.steps || DEFAULT_STEPS;
        setSeq({ grid: clonePattern(entry.data), bpm: entry.bpm || bpm, steps: loadedSteps });
    };

    const deletePattern = (name) => {
        setLibraryItems(library.filter((p) => p.name !== name));
    };

    const clearPattern = () => setSeq({ grid: emptyPattern(steps), bpm, steps });

    // RENDER: bounce one loop of the pattern to a loopable WAV and download it.
    // Rendered with a tail; the tail is folded back onto the start so decays that
    // ring past the loop boundary overlap the next loop seamlessly.
    const [rendering, setRendering] = React.useState(false);
    const renderLoop = async () => {
        setRendering(true);
        try {
            const secPerStep = 0.25 * 60 / (bpm || 120);   // 16th note
            const dur = steps * secPerStep;
            const rate = (window.OA_AUDIO_CTX && window.OA_AUDIO_CTX.sampleRate) || 44100;
            const Offline = window.OfflineAudioContext || window.webkitOfflineAudioContext;
            const tailSec = 2.0;
            const offline = new Offline(2, Math.max(1, Math.ceil((dur + tailSec) * rate)), rate);
            for (let step = 0; step < steps; step++) {
                const t = step * secPerStep;
                pattern.forEach((track, trkIdx) => {
                    const v = velOf(track[step]);
                    if (v > 0 && !mutes[trkIdx]) {
                        const vol = v / 100;
                        const entry = window.OA_DRUM_SAMPLES && window.OA_DRUM_SAMPLES[trkIdx];
                        if (entry && entry.buffer && window.oaPlayDrumSample) window.oaPlayDrumSample(offline, Object.assign({}, entry, { loop: false }), t, vol);
                        else if (window.oaPlayDrumVoice) window.oaPlayDrumVoice(offline, TRACKS[trkIdx], t, vol);
                    }
                });
            }
            const rendered = await offline.startRendering();
            const loopLen = Math.max(1, Math.round(dur * rate));
            const loopBuf = window.oaAudioCtx().createBuffer(2, loopLen, rate);
            for (let ch = 0; ch < 2; ch++) {
                const src = rendered.getChannelData(ch);
                const dst = loopBuf.getChannelData(ch);
                for (let i = 0; i < loopLen; i++) dst[i] = src[i] || 0;
                for (let j = 0; j + loopLen < src.length && j < loopLen; j++) dst[j] += src[loopLen + j]; // wrap tail
            }
            const blob = new Blob([window.oaEncodeWav(loopBuf)], { type: 'audio/wav' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url; a.download = `${safeLabel}_${bpm}bpm_${steps}steps.wav`;
            document.body.appendChild(a); a.click(); a.remove();
            setTimeout(() => URL.revokeObjectURL(url), 2000);
        } catch (e) { console.error('🛑 [Sequencer] render failed:', e); }
        setRendering(false);
    };

    return (
        <div style={{ padding: '12px', backgroundColor: 'rgba(18,18,18,0.28)', borderRadius: '4px', color: '#fff', border: '1px solid #333', width: '100%', boxSizing: 'border-box', marginTop: '10px' }}>
            <h3 style={{ margin: '0 0 8px 0', fontSize: '15px', color: '#ccc' }}>{label}</h3>
            <div style={{ display: 'flex', gap: '10px', marginBottom: '10px', alignItems: 'center' }}>
                <button
                    onClick={() => setRecording((r) => !r)}
                    title="Record: while playing, hit the Sampler pads to write them into the pattern at their velocity"
                    style={{ background: recording ? '#d32f2f' : '#5a1f1f', color: '#fff', border: recording ? '1px solid #ff8a80' : '1px solid #722', padding: '6px 15px', cursor: 'pointer', borderRadius: '3px', fontWeight: 'bold', boxShadow: recording ? '0 0 8px rgba(211,47,47,0.85)' : 'none' }}
                >
                    ● Rec{recording ? ' ●' : ''}
                </button>
                <button 
                    onClick={togglePlayback}
                    style={{ background: isPlaying ? '#ffb300' : '#388e3c', color: '#fff', border: 'none', padding: '6px 15px', cursor: 'pointer', borderRadius: '3px', fontWeight: 'bold' }}
                >
                    {isPlaying ? '■ Stop' : '► Play'}
                </button>
                <div style={{ marginLeft: '15px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '12px', color: '#aaa' }}>Tempo:</span>
                    <BpmKnob value={bpm} onChange={setBpm} flash={tapping} />
                    <button onClick={tapTempo} title="Tap to set tempo" style={{ background: tapping ? '#f4902c' : '#333', color: tapping ? '#111' : '#ccc', border: '1px solid #444', borderRadius: '3px', padding: '6px 10px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }}>TAP</button>
                </div>
                <div style={{ marginLeft: '15px', display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <span style={{ fontSize: '12px', color: '#aaa' }}>Steps:</span>
                    {STEP_OPTIONS.map((n) => (
                        <button key={n} onClick={() => setSteps(n)}
                            style={{ background: steps === n ? '#f4902c' : '#333', color: steps === n ? '#111' : '#ccc', border: '1px solid #444', padding: '4px 9px', cursor: 'pointer', borderRadius: '3px', fontWeight: 'bold', fontSize: '12px' }}>
                            {n}
                        </button>
                    ))}
                </div>
                <div style={{ marginLeft: 'auto', display: 'flex', gap: '6px' }}>
                    <button
                        onClick={renderLoop}
                        disabled={rendering}
                        title="Render this pattern to a loopable WAV file"
                        style={{ background: '#7b1fa2', color: '#fff', border: 'none', padding: '6px 12px', cursor: rendering ? 'wait' : 'pointer', borderRadius: '3px', fontWeight: 'bold' }}
                    >
                        {rendering ? '…rendering' : '⭳ RENDER'}
                    </button>
                    <button
                        onClick={savePattern}
                        style={{ background: '#1565c0', color: '#fff', border: 'none', padding: '6px 12px', cursor: 'pointer', borderRadius: '3px', fontWeight: 'bold' }}
                    >
                        ⭳ Save
                    </button>
                    <button
                        onClick={clearPattern}
                        style={{ background: '#333', color: '#ccc', border: 'none', padding: '6px 12px', cursor: 'pointer', borderRadius: '3px' }}
                    >
                        Clear
                    </button>
                </div>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', overflowX: 'auto', paddingBottom: '6px' }}>
                {TRACKS.map(({ name: trackName }, trkIdx) => {
                  const muted = mutes[trkIdx];
                  const tvol = trackVol[trkIdx] == null ? 1 : trackVol[trkIdx];
                  const volAngle = -135 + tvol * 270;   // knob indicator reflects the track volume
                  const openMenu = (e) => { e.stopPropagation(); setTrackMenu({ trkIdx, x: e.clientX, y: e.clientY }); };
                  return (
                    <div key={trackName} style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                        <div style={{ width: '110px', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'flex-start', gap: '5px', paddingRight: '6px', position: 'sticky', left: 0, background: '#161616', zIndex: 2 }}>
                            <button
                                onClick={() => toggleMute(trkIdx)}
                                title={muted ? `Unmute ${trackName}` : `Mute ${trackName}`}
                                style={{ width: '17px', height: '17px', flexShrink: 0, padding: 0, fontSize: '9px', fontWeight: 'bold', lineHeight: 1, cursor: 'pointer', borderRadius: '3px', border: `1px solid ${muted ? '#d32f2f' : '#444'}`, background: muted ? '#d32f2f' : '#2a2a2a', color: muted ? '#fff' : '#888' }}
                            >
                                M
                            </button>
                            <button
                                onClick={openMenu}
                                title={`${trackName} — vol ${Math.round(tvol * 100)} · click for sample / pitch / vol / pan`}
                                style={{ width: '17px', height: '17px', flexShrink: 0, padding: 0, borderRadius: '50%', border: '1px solid #555', background: 'radial-gradient(circle at 50% 35%, #555, #222)', cursor: 'pointer', position: 'relative' }}
                            >
                                <span style={{ position: 'absolute', inset: 0, transform: `rotate(${volAngle}deg)` }}>
                                    <span style={{ position: 'absolute', left: '50%', top: '1px', width: '2px', height: '6px', background: '#f4902c', transform: 'translateX(-50%)', borderRadius: '1px' }} />
                                </span>
                            </button>
                            <span
                                onClick={openMenu}
                                title={`${trackName} — click to pick a sample / pitch / vol / pan`}
                                style={{ fontSize: '11px', color: muted ? '#666' : '#ccc', textAlign: 'left', whiteSpace: 'nowrap', cursor: 'pointer' }}
                            >
                                {trackName}
                            </span>
                        </div>
                        <div style={{ display: 'flex', gap: '3px', background: '#0a0a0a', padding: '4px', borderRadius: '4px', border: '1px solid #222', opacity: muted ? 0.4 : 1 }}>
                            {[...Array(steps)].map((_, step) => {
                                const vel = velOf(pattern[trkIdx][step]);
                                const isLit = vel > 0;
                                const isBeat = step % 4 === 0;
                                const isCurrent = isPlaying && currentStep === step;
                                const isFading = activeFader && activeFader.trkIdx === trkIdx && activeFader.step === step;

                                return (
                                    <div key={step}
                                        data-oa-trk={trkIdx} data-oa-step={step}
                                        onPointerDown={(e) => onStepPointerDown(e, trkIdx, step)}
                                        title={isLit ? `Velocity ${vel} — ALT+drag to adjust` : 'Click/drag to paint · ALT+drag to set intensity'}
                                        style={{
                                            position: 'relative', overflow: 'hidden',
                                            width: '18px', height: '20px',
                                            backgroundColor: isCurrent ? '#fff' : (isBeat && !isLit ? '#333' : '#1a1a1a'),
                                            border: isFading ? '1px solid #fff' : (isLit ? '1px solid #ffa726' : '1px solid #111'),
                                            cursor: 'pointer', borderRadius: '2px', touchAction: 'none',
                                            boxShadow: isLit ? `0 0 4px rgba(244, 144, 44, ${0.2 + 0.4 * (vel / 100)})` : 'none',
                                        }}>
                                        {isLit && !isCurrent && (
                                            <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, height: `${Math.max(14, vel)}%`, background: `rgba(244, 144, 44, ${0.4 + 0.6 * (vel / 100)})`, pointerEvents: 'none' }} />
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                  );
                })}
            </div>

            <div style={{ marginTop: '10px', borderTop: '1px solid #333', paddingTop: '8px' }}>
                <div style={{ fontSize: '11px', color: '#888', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '6px' }}>
                    Patterns Library
                </div>
                {library.length === 0 ? (
                    <div style={{ fontSize: '12px', color: '#666', fontStyle: 'italic' }}>
                        No saved patterns yet — build a beat and hit Save.
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                        {library.map((entry) => (
                            <div key={entry.name} style={{ display: 'flex', alignItems: 'center', background: '#2a2a2a', borderRadius: '3px', border: '1px solid #444', overflow: 'hidden' }}>
                                <button
                                    onClick={() => loadPattern(entry)}
                                    title={`Load "${entry.name}"${entry.bpm ? ` @ ${entry.bpm} BPM` : ''}`}
                                    style={{ background: 'transparent', color: '#f4902c', border: 'none', padding: '5px 10px', cursor: 'pointer', fontSize: '12px' }}
                                >
                                    {entry.name}
                                </button>
                                <button
                                    onClick={() => deletePattern(entry.name)}
                                    title={`Delete "${entry.name}"`}
                                    style={{ background: 'transparent', color: '#777', border: 'none', borderLeft: '1px solid #444', padding: '5px 8px', cursor: 'pointer', fontSize: '12px' }}
                                >
                                    ✕
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {activeFader && (
                <div style={{ position: 'fixed', zIndex: 10000, pointerEvents: 'none',
                    left: Math.min(activeFader.x + 16, window.innerWidth - 90),
                    top: Math.min(Math.max(activeFader.y - 130, 8), window.innerHeight - 260),
                    width: '78px', background: '#1c1c1c', border: '1px solid #f4902c', borderRadius: '6px',
                    padding: '10px', boxShadow: '0 8px 30px rgba(0,0,0,0.75)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                    <div style={{ fontSize: '22px', fontWeight: 'bold', color: '#f4902c', lineHeight: 1 }}>{activeFader.vel}</div>
                    <div style={{ position: 'relative', width: '30px', height: '200px', background: '#0a0a0a', border: '1px solid #444', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, height: `${activeFader.vel}%`, background: 'linear-gradient(to top, #b96a1e, #f4902c)' }} />
                        <div style={{ position: 'absolute', left: '-2px', right: '-2px', bottom: `calc(${activeFader.vel}% - 2px)`, height: '4px', background: '#fff', borderRadius: '1px' }} />
                    </div>
                    <div style={{ fontSize: '9px', color: '#888', letterSpacing: '0.5px' }}>VELOCITY</div>
                </div>
            )}

            {trackMenu && (
                <TrackSampleMenu
                    trkIdx={trackMenu.trkIdx}
                    trackName={(TRACKS[trackMenu.trkIdx] && TRACKS[trackMenu.trkIdx].name) || ''}
                    anchor={{ x: trackMenu.x, y: trackMenu.y }}
                    version={trackVer}
                    vol={trackVol[trackMenu.trkIdx]}
                    pan={trackPan[trackMenu.trkIdx]}
                    onVol={(v) => setTrackVol((prev) => { const n = [...prev]; n[trackMenu.trkIdx] = v; return n; })}
                    onPan={(v) => setTrackPan((prev) => { const n = [...prev]; n[trackMenu.trkIdx] = v; return n; })}
                    onChange={() => setTrackVer((v) => v + 1)}
                    onBrowse={() => setBrowseTrack(trackMenu.trkIdx)}
                    onClose={() => setTrackMenu(null)}
                />
            )}
            {browseTrack != null && window.SoundBrowse && (
                <window.SoundBrowse
                    targetLabel={(TRACKS[browseTrack] && TRACKS[browseTrack].name) || ''}
                    onClose={() => setBrowseTrack(null)}
                    onChoose={(file, meta) => { loadTrackSample(browseTrack, file, meta); setBrowseTrack(null); }}
                />
            )}
        </div>
    );
};
window.Sequencer = Sequencer;
