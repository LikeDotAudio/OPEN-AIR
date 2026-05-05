const CMDP = ({ value = 0, onChange, size = 200 }) => {
    const [isDragging, setIsDragging] = React.useState(false);
    const center = size / 2;
    const radius = size / 2 - 20;

    const calculateAngle = (e) => {
        const svgRect = e.currentTarget.getBoundingClientRect();
        const mouseX = e.clientX - svgRect.left;
        const mouseY = e.clientY - svgRect.top;
        
        const dx = mouseX - center;
        const dy = mouseY - center;
        
        let angle = Math.atan2(dy, dx) * (180 / Math.PI);
        // Normalize angle so 0 is top
        angle += 90;
        if (angle < 0) angle += 360;
        return angle;
    };

    const handlePointerDown = (e) => {
        setIsDragging(true);
        e.target.setPointerCapture(e.pointerId);
        const newAngle = calculateAngle(e);
        onChange(newAngle);
    };

    const handlePointerMove = (e) => {
        if (!isDragging) return;
        const newAngle = calculateAngle(e);
        onChange(newAngle);
    };

    const handlePointerUp = (e) => {
        setIsDragging(false);
        e.target.releasePointerCapture(e.pointerId);
    };

    return (
        <div style={{ position: 'relative', width: size, height: size }}>
            <svg 
                width={size} 
                height={size} 
                style={{ touchAction: 'none', cursor: 'crosshair', overflow: 'visible' }}
                onPointerDown={handlePointerDown}
                onPointerMove={handlePointerMove}
                onPointerUp={handlePointerUp}
                onPointerCancel={handlePointerUp}
            >
                {/* Outer Track */}
                <circle 
                    cx={center} 
                    cy={center} 
                    r={radius} 
                    fill="none" 
                    stroke="#1a1a1a" 
                    strokeWidth="10" 
                />
                
                {/* Scale Ticks */}
                {Array.from({ length: 12 }).map((_, i) => (
                    <line 
                        key={i}
                        x1={center}
                        y1={center - radius + 5}
                        x2={center}
                        y2={center - radius - 5}
                        stroke="#555"
                        strokeWidth="2"
                        transform={`rotate(${i * 30}, ${center}, ${center})`}
                    />
                ))}

                {/* Rotating Handle */}
                <g transform={`rotate(${value}, ${center}, ${center})`}>
                    <line 
                        x1={center} 
                        y1={center} 
                        x2={center} 
                        y2={center - radius} 
                        stroke="#fff" 
                        strokeWidth="4" 
                        strokeLinecap="round" 
                    />
                    <circle 
                        cx={center} 
                        cy={center - radius} 
                        r="12" 
                        fill="#444" 
                        stroke="#222" 
                        strokeWidth="2" 
                    />
                </g>

                {/* Center Hub */}
                <circle cx={center} cy={center} r="20" fill="#333" stroke="#111" strokeWidth="3" />
            </svg>
        </div>
    );
};
window.CMDP = CMDP;