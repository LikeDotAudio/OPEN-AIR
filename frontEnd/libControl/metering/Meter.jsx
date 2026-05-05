// Custom hook for ballistic smoothing
function useBallistics(rawValueRef, canvasRef, min, max, width, height) {
    React.useEffect(() => {
        let displayValue = min;
        let peakValue = min;
        let peakHoldTimer = 0;
        
        let animationFrameId;

        const render = () => {
            const raw = rawValueRef.current;
            
            // Ballistics Logic: Fast attack, slower release
            if (raw > displayValue) {
                displayValue += (raw - displayValue) * 0.4; // Attack
            } else {
                displayValue -= (displayValue - raw) * 0.05; // Release
            }

            // Peak Hold Logic
            if (raw > peakValue) {
                peakValue = raw;
                peakHoldTimer = 60; // hold for 60 frames (~1 sec)
            } else {
                if (peakHoldTimer > 0) {
                    peakHoldTimer--;
                } else {
                    peakValue -= (peakValue - min) * 0.02; // Peak release
                }
            }

            // Draw to Canvas
            if (canvasRef.current) {
                const ctx = canvasRef.current.getContext('2d');
                ctx.clearRect(0, 0, width, height);

                // Draw background track
                ctx.fillStyle = '#111';
                ctx.fillRect(0, 0, width, height);

                const getValY = (val) => {
                    const percent = Math.max(0, Math.min(1, (val - min) / (max - min)));
                    return height - percent * height;
                };

                const displayY = getValY(displayValue);
                
                // Create gradient (Green -> Yellow -> Red)
                const gradient = ctx.createLinearGradient(0, height, 0, 0);
                gradient.addColorStop(0, '#0f0');
                gradient.addColorStop(0.7, '#ff0');
                gradient.addColorStop(1, '#f00');

                // Draw meter bar
                ctx.fillStyle = gradient;
                ctx.fillRect(0, displayY, width, height - displayY);

                // Draw Peak indicator
                const peakY = getValY(peakValue);
                ctx.fillStyle = '#fff';
                ctx.fillRect(0, peakY, width, 2);
            }

            animationFrameId = requestAnimationFrame(render);
        };

        render();

        return () => {
            cancelAnimationFrame(animationFrameId);
        };
    }, [min, max, width, height]);
}

const Meter = ({ value, min = 0, max = 100, width = 30, height = 300 }) => {
    const canvasRef = React.useRef(null);
    const rawValueRef = React.useRef(value);

    // Sync raw value to ref to bypass React rendering cycle
    React.useEffect(() => {
        rawValueRef.current = value;
    }, [value]);

    useBallistics(rawValueRef, canvasRef, min, max, width, height);

    return (
        <div style={{ border: '2px solid #222', padding: '2px', backgroundColor: '#000', borderRadius: '4px' }}>
            <canvas 
                ref={canvasRef} 
                width={width} 
                height={height} 
                style={{ display: 'block' }}
            />
        </div>
    );
};
window.Meter = Meter;