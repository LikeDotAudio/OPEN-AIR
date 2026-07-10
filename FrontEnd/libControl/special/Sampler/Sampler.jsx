const Sampler = ({ label = "MPC Sampler", centerVelocity = 100, edgeVelocity = 10, onHit = null }) => {
    // Shared drum kit — the SAME 16 voices the Sequencer uses (DrumKit.js).
    const KIT = window.OA_DRUM_KIT || [];

    // Per-pad loaded-sample file name (for display); null = uses the synth voice.
    // The decoded audio lives in window.OA_DRUM_SAMPLES so the Sequencer plays it
    // too. Seed from that shared store so pads loaded before a remount still show.
    const [sampleNames, setSampleNames] = React.useState(() =>
        Array(16).fill(null).map((_, i) =>
            (window.OA_DRUM_SAMPLES && window.OA_DRUM_SAMPLES[i]) ? '(loaded)' : null));

    // Side-car value per pad: velocity (0-100) of the most recent hit. Drives
    // playback volume AND the pad's visual glow.
    const [velocities, setVelocities] = React.useState(Array(16).fill(0));

    // Hidden file inputs, one per pad, triggered only on ALT+press.
    const fileInputs = React.useRef([]);

    // The standard MPC layout is bottom-left to top-right:
    // 13 14 15 16
    // 9  10 11 12
    // 5  6  7  8
    // 1  2  3  4
    const layout = [13, 14, 15, 16, 9, 10, 11, 12, 5, 6, 7, 8, 1, 2, 3, 4];

    // Load a sample onto a pad: decode to an AudioBuffer in the SHARED store so
    // both this pad and the Sequencer's matching track play it.
    const handleFile = async (index, file) => {
        if (!file) return;
        try {
            const arrayBuf = await file.arrayBuffer();
            const ctx = window.oaAudioCtx();
            const audioBuf = await ctx.decodeAudioData(arrayBuf);
            window.OA_DRUM_SAMPLES[index] = audioBuf;
            setSampleNames((prev) => { const n = [...prev]; n[index] = file.name; return n; });
        } catch (e) {
            console.error('🛑 [Sampler] Could not decode audio:', e);
        }
    };

    // Position-sensitive velocity: centre of the pad = centerVelocity, the edge =
    // edgeVelocity, smooth radial falloff (normalized by the inscribed radius).
    const computeVelocity = (e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const cx = rect.left + rect.width / 2;
        const cy = rect.top + rect.height / 2;
        const dx = e.clientX - cx;
        const dy = e.clientY - cy;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const radius = (Math.min(rect.width, rect.height) / 2) || 1;
        const d = Math.min(dist / radius, 1);
        const v = centerVelocity + (edgeVelocity - centerVelocity) * d;
        return Math.round(Math.max(0, Math.min(100, v)));
    };

    // A pad was struck: compute velocity, store it, trigger the drum (sample or
    // synth) at a volume scaled by the velocity, notify.
    const hitPad = (e, idx) => {
        const velocity = computeVelocity(e);
        setVelocities((prev) => { const n = [...prev]; n[idx] = velocity; return n; });
        if (window.oaTriggerDrum) window.oaTriggerDrum(idx, velocity / 100);
        if (typeof onHit === 'function') onHit(idx + 1, velocity);
        return velocity;
    };

    return (
        <div style={{ padding: '25px', backgroundColor: '#1e1e1e', borderRadius: '4px', color: '#fff', border: '1px solid #333', display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%', boxSizing: 'border-box' }}>
            <h3 style={{ margin: '0 0 20px 0', fontSize: '18px', color: '#ccc', textAlign: 'center', textTransform: 'uppercase', letterSpacing: '1px' }}>{label}</h3>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '18px', justifyContent: 'center', padding: '18px', background: '#0a0a0a', border: '1px solid #111', borderRadius: '8px' }}>
                {layout.map((padNum) => {
                    const idx = padNum - 1;
                    const name = (KIT[idx] && KIT[idx].name) || `Pad ${padNum}`;
                    const hasSample = !!sampleNames[idx];   // custom sample loaded
                    const vel = velocities[idx];            // side-car value (0-100)
                    const intensity = vel / 100;

                    // Every pad plays a sound; a loaded custom sample reads brighter
                    // orange, a synth-voice pad reads darker. Resting glow reflects
                    // the last hit's velocity.
                    const baseColor = hasSample ? '#f4902c' : '#3a3a3a';
                    const restShadow = vel > 0
                        ? `0 0 ${6 + 26 * intensity}px rgba(244, 144, 44, ${0.25 + 0.6 * intensity})`
                        : (hasSample ? '0 4px 8px rgba(0,0,0,0.4)' : 'inset 0 1px 3px rgba(0,0,0,0.6)');

                    return (
                        <div key={padNum} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            <button
                                title={hasSample ? `${name} — sample: ${sampleNames[idx]}\nALT+click to replace` : `${name} — synth voice\nALT+click to load a sample`}
                                onPointerDown={(e) => {
                                    // ALT+press opens the load dialog instead of playing.
                                    if (e.altKey) {
                                        e.preventDefault();
                                        const input = fileInputs.current[idx];
                                        if (input) input.click();
                                        return;
                                    }
                                    const v = hitPad(e, idx);
                                    const i = v / 100;
                                    e.currentTarget.style.transform = 'scale(0.95)';
                                    e.currentTarget.style.filter = `brightness(${0.75 + 0.6 * i})`;
                                    e.currentTarget.style.boxShadow = `0 0 ${8 + 30 * i}px rgba(244, 144, 44, ${0.35 + 0.65 * i})`;
                                }}
                                onPointerUp={(e) => {
                                    e.currentTarget.style.transform = 'scale(1)';
                                    e.currentTarget.style.filter = 'none';
                                    e.currentTarget.style.boxShadow = restShadow;
                                }}
                                onPointerLeave={(e) => {
                                    e.currentTarget.style.transform = 'scale(1)';
                                    e.currentTarget.style.filter = 'none';
                                    e.currentTarget.style.boxShadow = restShadow;
                                }}
                                style={{
                                    position: 'relative',
                                    width: '120px', height: '120px',
                                    backgroundColor: baseColor,
                                    border: '1px solid #000',
                                    borderTop: '1px solid #555',
                                    borderLeft: '1px solid #444',
                                    borderRadius: '6px',
                                    cursor: 'pointer',
                                    boxShadow: restShadow,
                                    color: hasSample ? '#000' : '#ccc',
                                    fontWeight: 'bold',
                                    display: 'flex', flexDirection: 'column',
                                    alignItems: 'center', justifyContent: 'center',
                                    textAlign: 'center', padding: '4px',
                                    transition: 'transform 0.05s, background-color 0.05s, box-shadow 0.05s, filter 0.05s',
                                    outline: 'none',
                                    touchAction: 'none'
                                }}
                            >
                                {/* Pad name = shared kit / Sequencer track name */}
                                <span style={{ fontSize: '15px', lineHeight: 1.1, wordBreak: 'break-word' }}>{name}</span>

                                {/* Tiny pad number, corner */}
                                <span style={{ position: 'absolute', bottom: '4px', left: '6px', fontSize: '9px', fontWeight: 'bold', opacity: 0.5 }}>
                                    {padNum}
                                </span>

                                {/* SMP badge when a custom sample is loaded */}
                                {hasSample && (
                                    <span style={{ position: 'absolute', bottom: '4px', right: '6px', fontSize: '8px', fontWeight: 'bold', opacity: 0.7, letterSpacing: '0.5px' }}>
                                        SMP
                                    </span>
                                )}

                                {/* Side-car velocity readout */}
                                {vel > 0 && (
                                    <span style={{ position: 'absolute', top: '4px', right: '6px', fontSize: '10px', fontWeight: 'bold', color: hasSample ? '#3a1f00' : '#f4902c', opacity: 0.9 }}>
                                        {vel}
                                    </span>
                                )}
                            </button>

                            {/* Hidden per-pad file input — only reachable via ALT+press */}
                            <input
                                ref={(el) => { fileInputs.current[idx] = el; }}
                                type="file"
                                accept="audio/*"
                                style={{ display: 'none' }}
                                onChange={(e) => handleFile(idx, e.target.files[0])}
                            />
                        </div>
                    );
                })}
            </div>

            <div style={{ marginTop: '14px', fontSize: '10px', color: '#666', textTransform: 'uppercase', letterSpacing: '0.5px', textAlign: 'center' }}>
                Velocity: centre {centerVelocity}% · edge {edgeVelocity}% (sets volume) · <b>ALT+click</b> a pad to load a sample
            </div>
        </div>
    );
};
window.Sampler = Sampler;
