// The 16-voice drum kit is shared with the Sampler (DrumKit.js) so a Sampler pad
// and the matching Sequencer track are the SAME voice — including any sample
// loaded onto that pad.
const TRACKS = window.OA_DRUM_KIT || [];
const STEP_OPTIONS = [4, 8, 16];   // selectable pattern lengths
const DEFAULT_STEPS = 16;
const LIBRARY_KEY = 'oaSequencerLibrary';

const emptyPattern = (steps) => Array(TRACKS.length).fill().map(() => Array(steps).fill(false));
const clonePattern = (p) => p.map((row) => [...row]);

const loadLibrary = () => {
    try {
        return JSON.parse(window.localStorage.getItem(LIBRARY_KEY)) || [];
    } catch (e) {
        return [];
    }
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

    // Scheduler runs in a stale RAF closure, so read the live step count via a ref.
    const stepsRef = React.useRef(steps);
    stepsRef.current = steps;

    const setPattern = (grid) => setSeq({ grid, bpm, steps });
    const setBpm = (nextBpm) => setSeq({ grid: pattern, bpm: nextBpm, steps });

    // Change pattern length (4/8/16): truncate or pad each track row to n steps.
    const setSteps = (n) => {
        const grid = pattern.map((row) => {
            const r = row.slice(0, n);
            while (r.length < n) r.push(false);
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
        const secondsPerBeat = 60.0 / bpm;
        nextNoteTimeRef.current += 0.25 * secondsPerBeat; // 16th note
        currentStepRef.current = (currentStepRef.current + 1) % stepsRef.current;
    };

    const scheduleNote = (stepNumber, time) => {
        // Only update UI if we're roughly at that time (sync UI to audio)
        requestAnimationFrame(() => setCurrentStep(stepNumber));
        
        const ctx = getAudioCtx();
        // Here we'd normally trigger sounds from the Sampler state.
        // For this demo, we'll synthesize simple beeps based on active tracks.
        pattern.forEach((track, trkIdx) => {
            if (track[stepNumber] && !mutesRef.current[trkIdx]) {
                // Play the shared voice: the Sampler's loaded sample for this
                // track if present, otherwise the synth voice.
                const buf = window.OA_DRUM_SAMPLES && window.OA_DRUM_SAMPLES[trkIdx];
                if (buf && window.oaPlayDrumSample) {
                    window.oaPlayDrumSample(ctx, buf, time, 1);
                } else if (window.oaPlayDrumVoice) {
                    window.oaPlayDrumVoice(ctx, TRACKS[trkIdx], time, 1);
                } else {
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.frequency.value = TRACKS[trkIdx].freq;
                    osc.type = TRACKS[trkIdx].type;
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    gain.gain.setValueAtTime(1, time);
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

    const toggleStep = (trkIdx, step) => {
        const newPattern = [...pattern];
        newPattern[trkIdx] = [...newPattern[trkIdx]];
        newPattern[trkIdx][step] = !newPattern[trkIdx][step];
        setPattern(newPattern);
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

    return (
        <div style={{ padding: '12px', backgroundColor: '#1e1e1e', borderRadius: '4px', color: '#fff', border: '1px solid #333', width: '100%', boxSizing: 'border-box', marginTop: '10px' }}>
            <h3 style={{ margin: '0 0 8px 0', fontSize: '15px', color: '#ccc' }}>{label}</h3>
            <div style={{ display: 'flex', gap: '10px', marginBottom: '10px', alignItems: 'center' }}>
                <button style={{ background: '#d32f2f', color: '#fff', border: 'none', padding: '6px 15px', cursor: 'pointer', borderRadius: '3px', fontWeight: 'bold', opacity: 0.5 }}>● Rec</button>
                <button 
                    onClick={togglePlayback}
                    style={{ background: isPlaying ? '#ffb300' : '#388e3c', color: '#fff', border: 'none', padding: '6px 15px', cursor: 'pointer', borderRadius: '3px', fontWeight: 'bold' }}
                >
                    {isPlaying ? '■ Stop' : '► Play'}
                </button>
                <div style={{ marginLeft: '15px', display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <span style={{ fontSize: '12px', color: '#aaa' }}>Tempo:</span>
                    <input type="number" value={bpm} onChange={(e) => setBpm(Number(e.target.value))} style={{ width: '50px', background: '#000', color: '#f4902c', border: '1px solid #444', textAlign: 'center' }} />
                    <span style={{ fontSize: '12px', color: '#aaa' }}>BPM</span>
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
                  return (
                    <div key={trackName} style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                        <div style={{ width: '86px', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '5px', paddingRight: '6px' }}>
                            <button
                                onClick={() => toggleMute(trkIdx)}
                                title={muted ? `Unmute ${trackName}` : `Mute ${trackName}`}
                                style={{ width: '17px', height: '17px', flexShrink: 0, padding: 0, fontSize: '9px', fontWeight: 'bold', lineHeight: 1, cursor: 'pointer', borderRadius: '3px', border: `1px solid ${muted ? '#d32f2f' : '#444'}`, background: muted ? '#d32f2f' : '#2a2a2a', color: muted ? '#fff' : '#888' }}
                            >
                                M
                            </button>
                            <span style={{ fontSize: '11px', color: muted ? '#666' : '#ccc', textAlign: 'right' }}>
                                {trackName}
                            </span>
                        </div>
                        <div style={{ display: 'flex', gap: '3px', background: '#0a0a0a', padding: '4px', borderRadius: '4px', border: '1px solid #222', opacity: muted ? 0.4 : 1 }}>
                            {[...Array(steps)].map((_, step) => {
                                const isLit = pattern[trkIdx][step];
                                const isBeat = step % 4 === 0;
                                const isCurrent = isPlaying && currentStep === step;

                                return (
                                    <div key={step} style={{
                                        width: '18px', height: '20px',
                                        backgroundColor: isCurrent ? '#fff' : (isLit ? '#f4902c' : (isBeat ? '#333' : '#1a1a1a')),
                                        border: isLit ? '1px solid #ffa726' : '1px solid #111',
                                        cursor: 'pointer',
                                        borderRadius: '2px',
                                        boxShadow: isLit ? '0 0 4px rgba(244, 144, 44, 0.5)' : 'none',
                                    }}
                                    onPointerDown={() => toggleStep(trkIdx, step)}
                                    ></div>
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
        </div>
    );
};
window.Sequencer = Sequencer;
