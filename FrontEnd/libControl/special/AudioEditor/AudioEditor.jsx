const AudioEditor = ({ label = "Wave Audio Editor" }) => {
    const canvasRef = React.useRef(null);
    const audioCtxRef = React.useRef(null);
    const [audioBuffer, setAudioBuffer] = React.useState(null);
    const [isPlaying, setIsPlaying] = React.useState(false);
    const sourceNodeRef = React.useRef(null);
    
    // Selection state (0.0 to 1.0)
    const [selection, setSelection] = React.useState({ start: 0.2, end: 0.8 });

    // Ensure AudioContext exists
    const getAudioCtx = () => {
        if (!audioCtxRef.current) {
            audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)();
        }
        return audioCtxRef.current;
    };

    const handleFile = async (file) => {
        if (!file) return;
        const ctx = getAudioCtx();
        const arrayBuffer = await file.arrayBuffer();
        const decodedBuffer = await ctx.decodeAudioData(arrayBuffer);
        setAudioBuffer(decodedBuffer);
        drawWaveform(decodedBuffer);
    };

    const drawWaveform = (buffer) => {
        const canvas = canvasRef.current;
        if (!canvas || !buffer) return;
        
        // Ensure canvas internal resolution matches display size
        canvas.width = canvas.clientWidth;
        canvas.height = canvas.clientHeight;
        
        const ctx = canvas.getContext('2d');
        const data = buffer.getChannelData(0); // Left channel
        const step = Math.ceil(data.length / canvas.width);
        const amp = canvas.height / 2;

        ctx.fillStyle = '#0a0a0a';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Center line
        ctx.strokeStyle = '#222';
        ctx.beginPath();
        ctx.moveTo(0, amp);
        ctx.lineTo(canvas.width, amp);
        ctx.stroke();
        
        ctx.strokeStyle = '#f4902c';
        ctx.beginPath();
        
        for (let i = 0; i < canvas.width; i++) {
            let min = 1.0;
            let max = -1.0;
            for (let j = 0; j < step; j++) {
                const datum = data[(i * step) + j]; 
                if (datum < min) min = datum;
                if (datum > max) max = datum;
            }
            ctx.moveTo(i, (1 + min) * amp);
            ctx.lineTo(i, (1 + max) * amp);
        }
        ctx.stroke();
    };

    const togglePlayback = () => {
        const ctx = getAudioCtx();
        if (isPlaying) {
            if (sourceNodeRef.current) {
                sourceNodeRef.current.stop();
                sourceNodeRef.current = null;
            }
            setIsPlaying(false);
        } else {
            if (!audioBuffer) return;
            const source = ctx.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(ctx.destination);
            
            // Calculate slice based on selection
            const startSec = selection.start * audioBuffer.duration;
            const endSec = selection.end * audioBuffer.duration;
            const duration = endSec - startSec;
            
            source.start(ctx.currentTime, startSec, duration);
            source.onended = () => setIsPlaying(false);
            
            sourceNodeRef.current = source;
            setIsPlaying(true);
        }
    };

    return (
        <div style={{ padding: '20px', backgroundColor: '#1e1e1e', borderRadius: '4px', color: '#fff', border: '1px solid #333', width: '100%', boxSizing: 'border-box' }}>
            <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', color: '#ccc' }}>{label}</h3>
            <div style={{ display: 'flex', gap: '10px', marginBottom: '10px', alignItems: 'center' }}>
                <input type="file" accept="audio/*" style={{ fontSize: '12px', color: '#aaa', width: '200px' }} onChange={(e) => handleFile(e.target.files[0])} />
                <button 
                    onClick={togglePlayback}
                    disabled={!audioBuffer}
                    style={{ background: isPlaying ? '#c00' : '#333', color: '#fff', border: 'none', padding: '5px 15px', cursor: audioBuffer ? 'pointer' : 'not-allowed', borderRadius: '3px', fontWeight: 'bold' }}
                >
                    {isPlaying ? 'Stop' : 'Play Slice'}
                </button>
                <div style={{ flexGrow: 1 }}></div>
                <span style={{ fontSize: '12px', color: '#666' }}>{audioBuffer ? `${audioBuffer.duration.toFixed(2)}s` : 'No audio loaded'}</span>
            </div>
            
            <div style={{ width: '100%', height: '140px', backgroundColor: '#0a0a0a', border: '1px solid #444', position: 'relative' }}>
                <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }}></canvas>
                
                {/* Simulated Selection Area Overlay */}
                {audioBuffer && (
                    <div style={{ 
                        position: 'absolute', 
                        left: `${selection.start * 100}%`, 
                        width: `${(selection.end - selection.start) * 100}%`, 
                        height: '100%', 
                        top: 0,
                        backgroundColor: 'rgba(244, 144, 44, 0.2)', 
                        borderLeft: '2px solid #f4902c', 
                        borderRight: '2px solid #f4902c',
                        pointerEvents: 'none' // For simplicity in this mockup, dragging is visual only
                    }}>
                    </div>
                )}
            </div>
            
            {audioBuffer && (
                <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '5px' }}>
                        <span style={{ fontSize: '10px', color: '#aaa' }}>START POINT</span>
                        <input type="range" min="0" max="0.99" step="0.01" value={selection.start} 
                            onChange={(e) => setSelection({ ...selection, start: Math.min(parseFloat(e.target.value), selection.end - 0.01) })}
                            style={{ width: '100%' }} />
                    </div>
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '5px' }}>
                        <span style={{ fontSize: '10px', color: '#aaa' }}>END POINT</span>
                        <input type="range" min="0.01" max="1" step="0.01" value={selection.end} 
                            onChange={(e) => setSelection({ ...selection, end: Math.max(parseFloat(e.target.value), selection.start + 0.01) })}
                            style={{ width: '100%' }} />
                    </div>
                </div>
            )}
        </div>
    );
};
window.AudioEditor = AudioEditor;
