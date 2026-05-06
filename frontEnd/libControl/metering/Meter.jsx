// Custom hook for ballistic smoothing
function useBallistics(rawValueRef, canvasRef, min, max, width, height, config) {
    React.useEffect(() => {
        let displayValue = min;
        let peakValue = min;
        let peakHoldTimer = 0;
        
        let animationFrameId;

        const render = () => {
            const raw = rawValueRef.current;
            
            // Ballistics Logic: Configurable attack/release
            const attack = config?.behavior?.attack || 0.4;
            const release = config?.behavior?.release || 0.05;

            if (raw > displayValue) {
                displayValue += (raw - displayValue) * attack; 
            } else {
                displayValue -= (displayValue - raw) * release;
            }

            // Peak Hold Logic
            const peakHoldFrames = config?.behavior?.peak_hold_frames || 60;
            if (raw > peakValue) {
                peakValue = raw;
                peakHoldTimer = peakHoldFrames;
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
                const bgColor = config?.cosmetics?.colors?.background || '#111';
                ctx.fillStyle = bgColor;
                ctx.fillRect(0, 0, width, height);

                const range = (max - min) || 1;
                const getValY = (val) => {
                    const percent = Math.max(0, Math.min(1, (val - min) / range));
                    return height - percent * height;
                };

                const displayY = getValY(displayValue);
                
                // Dynamic gradient creation based on JSON cosmetics or defaults
                const primaryColor = config?.cosmetics?.colors?.primary || '#0f0';
                const warningColor = config?.cosmetics?.colors?.warning || '#ff0';
                const dangerColor = config?.cosmetics?.colors?.danger || '#f00';

                const gradient = ctx.createLinearGradient(0, height, 0, 0);
                gradient.addColorStop(0, primaryColor);
                gradient.addColorStop(0.7, warningColor);
                gradient.addColorStop(1, dangerColor);

                // Draw meter bar
                ctx.fillStyle = gradient;
                ctx.fillRect(0, displayY, width, height - displayY);

                // Draw Scale Lines
                ctx.fillStyle = '#000';
                for(let i=0; i<10; i++) {
                    ctx.fillRect(0, height - (height/10)*i, width, 1);
                }

                // Draw Peak indicator
                const peakY = getValY(peakValue);
                ctx.fillStyle = config?.cosmetics?.colors?.peak || '#fff';
                ctx.fillRect(0, peakY, width, 2);
            }

            animationFrameId = requestAnimationFrame(render);
        };

        render();

        return () => {
            cancelAnimationFrame(animationFrameId);
        };
    }, [min, max, width, height, config]);
}

const Meter = ({ value, config }) => {
    const min = config?.domain?.primary?.min !== undefined ? config.domain.primary.min : -60;
    const max = config?.domain?.primary?.max !== undefined ? config.domain.primary.max : 10;
    
    // Smart scaling logic: prefer width from config, fallback to default sizes
    const width = config?.geometry?.width || 30;
    const height = config?.geometry?.height || 300;

    const canvasRef = React.useRef(null);
    const rawValueRef = React.useRef(value !== undefined && value !== null ? value : min);

    // Sync raw value to ref to bypass React rendering cycle
    React.useEffect(() => {
        rawValueRef.current = value !== undefined && value !== null ? value : min;
    }, [value, min]);

    useBallistics(rawValueRef, canvasRef, min, max, width, height, config);

    return (
        <div style={{ 
            border: '2px solid #222', 
            padding: '2px', 
            backgroundColor: '#000', 
            borderRadius: '4px',
            boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.8)'
        }}>
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