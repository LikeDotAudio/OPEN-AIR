// 16 Tracks, each with a name, synth pitch (Hz) and oscillator type
const TRACKS = [
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
const STEP_COUNT = 16;
const LIBRARY_KEY = 'oaSequencerLibrary';

const emptyPattern = () => Array(TRACKS.length).fill().map(() => Array(STEP_COUNT).fill(false));
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
    const [seq, setSeq] = window.useMqttState(patternTopic, { grid: emptyPattern(), bpm: 120 });
    const pattern = (seq && seq.grid) || emptyPattern();
    const bpm = (seq && seq.bpm) || 120;
    const setPattern = (grid) => setSeq({ grid, bpm });
    const setBpm = (nextBpm) => setSeq({ grid: pattern, bpm: nextBpm });

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
            audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)();
        }
        return audioCtxRef.current;
    };

    const nextNote = () => {
        const secondsPerBeat = 60.0 / bpm;
        nextNoteTimeRef.current += 0.25 * secondsPerBeat; // 16th note
        currentStepRef.current = (currentStepRef.current + 1) % STEP_COUNT;
    };

    const scheduleNote = (stepNumber, time) => {
        // Only update UI if we're roughly at that time (sync UI to audio)
        requestAnimationFrame(() => setCurrentStep(stepNumber));
        
        const ctx = getAudioCtx();
        // Here we'd normally trigger sounds from the Sampler state.
        // For this demo, we'll synthesize simple beeps based on active tracks.
        pattern.forEach((track, trkIdx) => {
            if (track[stepNumber]) {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                
                // Different pitch/timbre per track
                osc.frequency.value = TRACKS[trkIdx].freq;
                osc.type = TRACKS[trkIdx].type;
                
                osc.connect(gain);
                gain.connect(ctx.destination);
                
                // Basic decay envelope
                gain.gain.setValueAtTime(1, time);
                gain.gain.exponentialRampToValueAtTime(0.001, time + 0.1);
                
                osc.start(time);
                osc.stop(time + 0.1);
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
        const entry = { name, bpm, data: clonePattern(pattern) };
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
        setSeq({ grid: clonePattern(entry.data), bpm: entry.bpm || bpm });
    };

    const deletePattern = (name) => {
        setLibraryItems(library.filter((p) => p.name !== name));
    };

    const clearPattern = () => setPattern(emptyPattern());

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
                {TRACKS.map(({ name: trackName }, trkIdx) => (
                    <div key={trackName} style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                        <div style={{ width: '54px', fontSize: '11px', color: '#ccc', textAlign: 'right', paddingRight: '8px' }}>
                            {trackName}
                        </div>
                        <div style={{ display: 'flex', gap: '3px', background: '#0a0a0a', padding: '4px', borderRadius: '4px', border: '1px solid #222' }}>
                            {[...Array(STEP_COUNT)].map((_, step) => {
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
                ))}
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
