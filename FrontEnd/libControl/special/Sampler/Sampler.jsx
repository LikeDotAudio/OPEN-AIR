const Sampler = ({ label = "MPC Sampler" }) => {
    // Array to store ObjectURLs of loaded audio files
    const [samples, setSamples] = React.useState(Array(16).fill(null));
    
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

    // Play the assigned sound
    const playSample = (index) => {
        const url = samples[index];
        if (url) {
            // In a real production app, you'd decode this into an AudioBuffer using the AudioContext
            // for lower latency. We use the standard Audio object here for simplicity in this mockup.
            const audio = new Audio(url);
            audio.play();
        }
    };

    return (
        <div style={{ padding: '25px', backgroundColor: '#1e1e1e', borderRadius: '4px', color: '#fff', border: '1px solid #333', display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%', boxSizing: 'border-box' }}>
            <h3 style={{ margin: '0 0 20px 0', fontSize: '18px', color: '#ccc', textAlign: 'center', textTransform: 'uppercase', letterSpacing: '1px' }}>{label}</h3>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '15px', justifyContent: 'center', padding: '15px', background: '#0a0a0a', border: '1px solid #111', borderRadius: '8px' }}>
                {layout.map((padNum) => {
                    const idx = padNum - 1;
                    const hasSample = !!samples[idx];
                    
                    return (
                        <div key={padNum} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            <button 
                                onPointerDown={(e) => {
                                    e.currentTarget.style.transform = 'scale(0.95)';
                                    e.currentTarget.style.backgroundColor = hasSample ? '#ffa726' : '#555';
                                    e.currentTarget.style.boxShadow = hasSample ? '0 0 15px rgba(244, 144, 44, 0.8)' : 'inset 0 2px 4px rgba(0,0,0,0.5)';
                                    playSample(idx);
                                }}
                                onPointerUp={(e) => {
                                    e.currentTarget.style.transform = 'scale(1)';
                                    e.currentTarget.style.backgroundColor = hasSample ? '#f4902c' : '#333';
                                    e.currentTarget.style.boxShadow = hasSample ? '0 4px 8px rgba(0,0,0,0.4)' : 'inset 0 1px 3px rgba(0,0,0,0.6)';
                                }}
                                onPointerLeave={(e) => {
                                    e.currentTarget.style.transform = 'scale(1)';
                                    e.currentTarget.style.backgroundColor = hasSample ? '#f4902c' : '#333';
                                    e.currentTarget.style.boxShadow = hasSample ? '0 4px 8px rgba(0,0,0,0.4)' : 'inset 0 1px 3px rgba(0,0,0,0.6)';
                                }}
                                style={{
                                    width: '80px', height: '80px', 
                                    backgroundColor: hasSample ? '#f4902c' : '#333',
                                    border: '1px solid #000', 
                                    borderTop: '1px solid #555',
                                    borderLeft: '1px solid #444',
                                    borderRadius: '6px', 
                                    cursor: 'pointer',
                                    boxShadow: hasSample ? '0 4px 8px rgba(0,0,0,0.4)' : 'inset 0 1px 3px rgba(0,0,0,0.6)',
                                    color: hasSample ? '#000' : '#888', 
                                    fontWeight: 'bold',
                                    fontSize: '16px',
                                    transition: 'transform 0.05s, background-color 0.05s, box-shadow 0.05s',
                                    outline: 'none',
                                    touchAction: 'none' // Prevent scrolling on mobile drag
                                }}
                            >
                                {padNum}
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
        </div>
    );
};
window.Sampler = Sampler;
