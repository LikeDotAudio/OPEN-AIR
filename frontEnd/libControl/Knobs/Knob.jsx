const Knob = ({ value, onChange, min = 0, max = 100, size = 80 }) => {
    const [isDragging, setIsDragging] = React.useState(false);
    const startYRef = React.useRef(0);
    const startValRef = React.useRef(0);

    const minAngle = -135;
    const maxAngle = 135;
    
    const clamp = (val, min, max) => Math.max(min, Math.min(max, val));

    const handlePointerDown = (e) => {
        setIsDragging(true);
        startYRef.current = e.clientY;
        startValRef.current = value;
        e.target.setPointerCapture(e.pointerId);
    };

    const handlePointerMove = (e) => {
        if (!isDragging) return;
        const deltaY = startYRef.current - e.clientY;
        // Sensitivity: 1 pixel = 1 unit
        const range = max - min;
        const deltaVal = (deltaY / 100) * range; 
        const newVal = clamp(startValRef.current + deltaVal, min, max);
        onChange(newVal);
    };

    const handlePointerUp = (e) => {
        setIsDragging(false);
        e.target.releasePointerCapture(e.pointerId);
    };

    const percentage = (value - min) / (max - min);
    const angle = minAngle + percentage * (maxAngle - minAngle);

    const radius = size / 2;
    const center = size / 2;

    return (
        <svg 
            width={size} 
            height={size} 
            style={{ touchAction: 'none', cursor: 'ns-resize' }}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onPointerCancel={handlePointerUp}
        >
            <circle cx={center} cy={center} r={radius - 2} fill="#333" stroke="#111" strokeWidth="4" />
            
            {/* Ticks/Scale indicator (optional) */}
            <circle 
                cx={center} 
                cy={center} 
                r={radius - 8} 
                fill="none" 
                stroke="#444" 
                strokeWidth="2" 
                strokeDasharray="4 6" 
            />

            <g transform={`rotate(${angle}, ${center}, ${center})`}>
                <circle cx={center} cy={center} r={radius - 12} fill="#555" />
                <line 
                    x1={center} 
                    y1={center} 
                    x2={center} 
                    y2={12} 
                    stroke="#fff" 
                    strokeWidth="3" 
                    strokeLinecap="round" 
                />
            </g>
        </svg>
    );
};
window.Knob = Knob;