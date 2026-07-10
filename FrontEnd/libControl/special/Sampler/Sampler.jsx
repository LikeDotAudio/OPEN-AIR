const Sampler = ({ label = "MPC Sampler", centerVelocity = 100, edgeVelocity = 10, onHit = null }) => {
    // Array to store ObjectURLs of loaded audio files
    const [samples, setSamples] = React.useState(Array(16).fill(null));

    // Side-car value per pad: the velocity (0-100) of the most recent hit.
    // 0 = idle / never hit. Drives playback volume AND the pad's visual glow.
    const [velocities, setVelocities] = React.useState(Array(16).fill(0));

    // The standard MPC layout is bottom-left to top-right:
    // 13 14 15 16
    // 9  10 11 12
    // 5  6  7  8
    // 1  2  3  4
    const layout = [13, 14, 15, 16, 9, 10, 11, 12, 5, 6, 7, 8, 1, 2, 3, 4];

    // Handle file input for a specific pad
    const handleFile = (index, file) => {
        if (!file) return;
        const newSamples = [...samples];

        // Revoke the old URL to avoid memory leaks if a sample is replaced
        if (newSamples[index]) {
            URL.revokeObjectURL(newSamples[index]);
        }

        // Create a new URL that the Audio API can consume
        newSamples[index] = URL.createObjectURL(file);
        setSamples(newSamples);
    };

    // Position-sensitive velocity: map WHERE inside the pad the user touched to a
    // velocity value. Dead-centre yields `centerVelocity`, the pad edge yields
    // `edgeVelocity`, with a smooth radial falloff in between. Distance is
    // normalized by the pad's inscribed radius (half the smaller side) so every
    // edge midpoint reaches edgeVelocity and corners clamp to it too.
    const computeVelocity = (e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const cx = rect.left + rect.width / 2;
        const cy = rect.top + rect.height / 2;
        const dx = e.clientX - cx;
        const dy = e.clientY - cy;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const radius = (Math.min(rect.width, rect.height) / 2) || 1;
        const d = Math.min(dist / radius, 1);           // 0 at centre → 1 at edge
        const v = centerVelocity + (edgeVelocity - centerVelocity) * d;
        return Math.round(Math.max(0, Math.min(100, v)));
    };

    // Play the assigned sound at an intensity scaled by the hit velocity.
    const playSample = (index, velocity) => {
        const url = samples[index];
        if (url) {
            // In a real production app, you'd decode this into an AudioBuffer using the AudioContext
            // for lower latency. We use the standard Audio object here for simplicity in this mockup.
            const audio = new Audio(url);
            audio.volume = Math.max(0, Math.min(1, velocity / 100));
            audio.play();
        }
    };

    // A pad was struck: compute velocity, store the side-car value, play, notify.
    const hitPad = (e, idx) => {
        const velocity = computeVelocity(e);
        setVelocities((prev) => {
            const next = [...prev];
            next[idx] = velocity;
            return next;
        });
        playSample(idx, velocity);
        if (typeof onHit === 'function') onHit(idx + 1, velocity);
        return velocity;
    };

    return (
        <div style={{ padding: '25px', backgroundColor: '#1e1e1e', borderRadius: '4px', color: '#fff', border: '1px solid #333', display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%', boxSizing: 'border-box' }}>
            <h3 style={{ margin: '0 0 20px 0', fontSize: '18px', color: '#ccc', textAlign: 'center', textTransform: 'uppercase', letterSpacing: '1px' }}>{label}</h3>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '15px', justifyContent: 'center', padding: '15px', background: '#0a0a0a', border: '1px solid #111', borderRadius: '8px' }}>
                {layout.map((padNum) => {
                    const idx = padNum - 1;
                    const hasSample = !!samples[idx];
                    const vel = velocities[idx];              // side-car value (0-100)
                    const intensity = vel / 100;              // 0 → 1

                    // Resting glow reflects the LAST hit's velocity so you can see
                    // how hard each pad was struck.
                    const restShadow = hasSample
                        ? (vel > 0
                            ? `0 0 ${6 + 26 * intensity}px rgba(244, 144, 44, ${0.25 + 0.6 * intensity})`
                            : '0 4px 8px rgba(0,0,0,0.4)')
                        : 'inset 0 1px 3px rgba(0,0,0,0.6)';

                    return (
                        <div key={padNum} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            <button
                                onPointerDown={(e) => {
                                    const v = hitPad(e, idx);
                                    const i = v / 100;
                                    e.currentTarget.style.transform = 'scale(0.95)';
                                    // Brightness of the pressed pad tracks the velocity.
                                    e.currentTarget.style.backgroundColor = hasSample ? '#ffa726' : '#555';
                                    e.currentTarget.style.filter = `brightness(${0.75 + 0.6 * i})`;
                                    e.currentTarget.style.boxShadow = hasSample
                                        ? `0 0 ${8 + 30 * i}px rgba(244, 144, 44, ${0.35 + 0.65 * i})`
                                        : 'inset 0 2px 4px rgba(0,0,0,0.5)';
                                }}
                                onPointerUp={(e) => {
                                    e.currentTarget.style.transform = 'scale(1)';
                                    e.currentTarget.style.filter = 'none';
                                    e.currentTarget.style.backgroundColor = hasSample ? '#f4902c' : '#333';
                                    e.currentTarget.style.boxShadow = restShadow;
                                }}
                                onPointerLeave={(e) => {
                                    e.currentTarget.style.transform = 'scale(1)';
                                    e.currentTarget.style.filter = 'none';
                                    e.currentTarget.style.backgroundColor = hasSample ? '#f4902c' : '#333';
                                    e.currentTarget.style.boxShadow = restShadow;
                                }}
                                style={{
                                    position: 'relative',
                                    width: '80px', height: '80px',
                                    backgroundColor: hasSample ? '#f4902c' : '#333',
                                    border: '1px solid #000',
                                    borderTop: '1px solid #555',
                                    borderLeft: '1px solid #444',
                                    borderRadius: '6px',
                                    cursor: 'pointer',
                                    boxShadow: restShadow,
                                    color: hasSample ? '#000' : '#888',
                                    fontWeight: 'bold',
                                    fontSize: '16px',
                                    transition: 'transform 0.05s, background-color 0.05s, box-shadow 0.05s, filter 0.05s',
                                    outline: 'none',
                                    touchAction: 'none' // Prevent scrolling on mobile drag
                                }}
                            >
                                {padNum}
                                {/* Side-car velocity readout: shows the last hit strength */}
                                {vel > 0 && (
                                    <span style={{
                                        position: 'absolute', top: '3px', right: '4px',
                                        fontSize: '9px', fontWeight: 'bold', lineHeight: 1,
                                        color: hasSample ? '#3a1f00' : '#f4902c',
                                        opacity: 0.9
                                    }}>
                                        {vel}
                                    </span>
                                )}
                            </button>

                            {/* Hidden file input wrapped in a styled label */}
                            <label style={{
                                marginTop: '10px', fontSize: '10px', color: hasSample ? '#f4902c' : '#888',
                                cursor: 'pointer', background: '#222', padding: '3px 8px',
                                borderRadius: '3px', border: hasSample ? '1px solid #f4902c' : '1px solid #444',
                                textTransform: 'uppercase', transition: 'all 0.2s'
                            }}>
                                {hasSample ? "Change" : "Load"}
                                <input
                                    type="file"
                                    accept="audio/*"
                                    style={{ display: 'none' }}
                                    onChange={(e) => handleFile(idx, e.target.files[0])}
                                />
                            </label>
                        </div>
                    );
                })}
            </div>

            <div style={{ marginTop: '14px', fontSize: '10px', color: '#666', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Velocity: centre {centerVelocity}% · edge {edgeVelocity}% — hit closer to centre = harder
            </div>
        </div>
    );
};
window.Sampler = Sampler;
