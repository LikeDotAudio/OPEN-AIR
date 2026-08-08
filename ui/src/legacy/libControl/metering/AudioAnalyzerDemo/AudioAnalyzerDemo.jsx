/**
 * Header: AudioAnalyzerDemo.jsx
 * Purpose: AudioAnalyzerDemo component or utility.
 * Description: Handles logic and rendering for AudioAnalyzerDemo component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// Inline comment: Logic for AudioAnalyzerDemo
const AudioAnalyzerDemo = ({ config }) => {
    const videoRef = React.useRef(null);
    const audioCtxRef = React.useRef(null);
    const analyserRef = React.useRef(null);
    const sourceRef = React.useRef(null);
    const animFrameRef = React.useRef(null);

    const [rmsVal, setRmsVal] = React.useState(-60);
    const [eqCsv, setEqCsv] = React.useState("");

    React.useEffect(() => {
        if (!videoRef.current) return;
        const video = videoRef.current;

        const handlePlay = () => {
            if (!audioCtxRef.current) {
                const AudioContext = window.AudioContext || window.webkitAudioContext;
                const ctx = new AudioContext();
                audioCtxRef.current = ctx;
                
                analyserRef.current = ctx.createAnalyser();
                analyserRef.current.fftSize = 512;
                analyserRef.current.smoothingTimeConstant = 0.8;

                sourceRef.current = ctx.createMediaElementSource(video);
                sourceRef.current.connect(analyserRef.current);
                analyserRef.current.connect(ctx.destination);
            }
            if (audioCtxRef.current.state === 'suspended') {
                audioCtxRef.current.resume();
            }

            const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
            
            const updateLoop = () => {
                analyserRef.current.getByteFrequencyData(dataArray);
                
                // Calculate RMS for meters (-60 to 0 dB)
                let sum = 0;
                for (let i = 0; i < dataArray.length; i++) {
                    const norm = dataArray[i] / 255.0;
                    sum += norm * norm;
                }
                const rms = Math.sqrt(sum / dataArray.length);
                const db = rms > 0 ? 20 * Math.log10(rms) : -60;
                setRmsVal(Math.max(-60, db));

                // Calculate EQ curve (log scaled frequencies)
                const sampleRate = audioCtxRef.current.sampleRate;
                const binSize = (sampleRate / 2) / analyserRef.current.frequencyBinCount;
                
                let csv = "";
                // Pick specific frequencies to plot on the 20-20k log scale
                const targetFreqs = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000];
                for (const freq of targetFreqs) {
                    const bin = Math.min(dataArray.length - 1, Math.floor(freq / binSize));
                    const val = dataArray[bin];
                    // Map 0-255 to -32 to 32 dB
                    const mappedDb = (val / 255.0) * 64 - 32;
                    csv += `${freq},${mappedDb.toFixed(1)}\n`;
                }
                setEqCsv(csv);

                animFrameRef.current = requestAnimationFrame(updateLoop);
            };
            
            updateLoop();
        };

        const handlePause = () => {
            if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
        };

        video.addEventListener('play', handlePlay);
        video.addEventListener('pause', handlePause);

        return () => {
            video.removeEventListener('play', handlePlay);
            video.removeEventListener('pause', handlePause);
            if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
        };
    }, []);

    const layout = config?.layout || { width: '100%', height: '100%' };

    // Fake configs for the meters to look good
    const barConfig = {
        domain: { primary: { min: -60, max: 0 } },
        geometry: { width: 50, height: 350 },
        cosmetics: { colors: { fill_normal: "#4CAF50", fill_warn: "#FFC107", fill_danger: "#F44336" } }
    };
    
    const needleConfig = {
        domain: { primary: { min: -60, max: 0 } },
        geometry: { width: 350, height: 200 },
        cosmetics: { face_color: "#e2ddc8" }
    };

    const eqConfig = {
        geometry: { width: 500, height: 350 },
        datasets: []
    };

    return (
        <div style={{ width: layout.width, height: layout.height, display: 'flex', flexDirection: 'column', gap: '20px', padding: '20px', backgroundColor: '#111', color: '#fff' }}>
            <div style={{ display: 'flex', gap: '20px' }}>
                <video 
                    ref={videoRef} 
                    src="./images/demo_video.mp4" 
                    controls 
                    crossOrigin="anonymous"
                    style={{ width: '400px', borderRadius: '8px', border: '2px solid #333' }}
                />
                <div style={{ flex: 1 }}>
                    <h3>Real-Time Analysis Demo</h3>
                    <p style={{ color: '#aaa' }}>Web Audio API captures the video's audio stream, calculates RMS and FFT, and drives the meters below.</p>
                </div>
            </div>
            
            <div style={{ display: 'flex', gap: '40px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
                <div>
                    <h4 style={{ textAlign: 'center', marginBottom: '10px', color: '#888' }}>Bar Graph</h4>
                    {window.MeterBarGraph ? <window.MeterBarGraph value={rmsVal} config={barConfig} /> : null}
                </div>
                <div>
                    <h4 style={{ textAlign: 'center', marginBottom: '10px', color: '#888' }}>Needle Meter</h4>
                    {window.NeedleMeter ? <window.NeedleMeter value={rmsVal} config={needleConfig} /> : null}
                </div>
                <div>
                    <h4 style={{ textAlign: 'center', marginBottom: '10px', color: '#888' }}>Equalization Graph</h4>
                    {window.Equalization ? <window.Equalization value={eqCsv} config={eqConfig} /> : null}
                </div>
            </div>
        </div>
    );
};

window.AudioAnalyzerDemo = AudioAnalyzerDemo;
