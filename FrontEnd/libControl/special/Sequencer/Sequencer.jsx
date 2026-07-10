const Sequencer = ({ label = "Pattern Sequencer" }) => {
    const audioCtxRef = React.useRef(null);
    const [isPlaying, setIsPlaying] = React.useState(false);
    const [bpm, setBpm] = React.useState(120);
    const [currentStep, setCurrentStep] = React.useState(0);
    
    // 4 Tracks, 16 steps each
    const [pattern, setPattern] = React.useState(
        Array(4).fill().map(() => Array(16).fill(false))
    );
    
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
        currentStepRef.current = (currentStepRef.current + 1) % 16;
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
                
                // Different pitch per track (Kick, Snare, Hi-Hat, Perc)
                osc.frequency.value = [60, 200, 800, 400][trkIdx];
                if (trkIdx === 2) osc.type = 'square'; // Hi-hat
                
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

    return (
        <div style={{ padding: '20px', backgroundColor: '#1e1e1e', borderRadius: '4px', color: '#fff', border: '1px solid #333', width: '100%', boxSizing: 'border-box', marginTop: '10px' }}>
            <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', color: '#ccc' }}>{label}</h3>
            <div style={{ display: 'flex', gap: '10px', marginBottom: '15px', alignItems: 'center' }}>
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
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', overflowX: 'auto', paddingBottom: '10px' }}>
                {['Kick', 'Snare', 'Hi-Hat', 'Perc'].map((trackName, trkIdx) => (
                    <div key={trackName} style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                        <div style={{ width: '60px', fontSize: '12px', color: '#ccc', textAlign: 'right', paddingRight: '10px' }}>
                            {trackName}
                        </div>
                        <div style={{ display: 'flex', gap: '4px', background: '#0a0a0a', padding: '5px', borderRadius: '4px', border: '1px solid #222' }}>
                            {[...Array(16)].map((_, step) => {
                                const isLit = pattern[trkIdx][step];
                                const isBeat = step % 4 === 0;
                                const isCurrent = isPlaying && currentStep === step;
                                
                                return (
                                    <div key={step} style={{ 
                                        width: '24px', height: '32px', 
                                        backgroundColor: isCurrent ? '#fff' : (isLit ? '#f4902c' : (isBeat ? '#333' : '#1a1a1a')), 
                                        border: isLit ? '1px solid #ffa726' : '1px solid #111', 
                                        cursor: 'pointer', 
                                        borderRadius: '2px',
                                        boxShadow: isLit ? '0 0 5px rgba(244, 144, 44, 0.5)' : 'none',
                                    }}
                                    onPointerDown={() => toggleStep(trkIdx, step)}
                                    ></div>
                                );
                            })}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};
window.Sequencer = Sequencer;
