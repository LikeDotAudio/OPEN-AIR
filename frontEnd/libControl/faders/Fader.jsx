const Fader = ({ value, onChange, min = 0, max = 100, height = 300, width = 60 }) => {
    const trackRef = React.useRef(null);
    const [isDragging, setIsDragging] = React.useState(false);

    const handlePointerDown = (e) => {
        setIsDragging(true);
        updateValue(e.clientY);
        e.target.setPointerCapture(e.pointerId);
    };

    const handlePointerMove = (e) => {
        if (isDragging) {
            updateValue(e.clientY);
        }
    };

    const handlePointerUp = (e) => {
        setIsDragging(false);
        e.target.releasePointerCapture(e.pointerId);
    };

    const updateValue = (clientY) => {
        if (!trackRef.current) return;
        const rect = trackRef.current.getBoundingClientRect();
        // Calculate percentage from bottom
        let percent = 1 - (clientY - rect.top) / rect.height;
        percent = Math.max(0, Math.min(1, percent));
        const newValue = min + percent * (max - min);
        onChange(newValue);
    };

    const thumbHeight = 30;
    const thumbY = height - ((value - min) / (max - min)) * height - thumbHeight / 2;

    // Render scale ticks
    const ticks = [];
    for (let i = 0; i <= 10; i++) {
        const tickY = height - (i / 10) * height;
        ticks.push(
            <line key={i} x1="5" y1={tickY} x2="15" y2={tickY} stroke="#aaa" strokeWidth="2" />
        );
    }

    return (
        <svg 
            width={width} 
            height={height + thumbHeight} 
            style={{ touchAction: 'none', cursor: 'pointer', overflow: 'visible' }}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onPointerCancel={handlePointerUp}
        >
            <g transform={`translate(0, ${thumbHeight / 2})`} ref={trackRef}>
                {/* Track */}
                <rect x={width / 2 - 4} y="0" width="8" height={height} fill="#1a1a1a" rx="4" />
                <rect x={width / 2 - 2} y="0" width="4" height={height} fill="#000" rx="2" />
                
                {/* Scale Ticks */}
                {ticks}

                {/* Thumb */}
                <g transform={`translate(${width / 2}, ${thumbY + thumbHeight/2})`}>
                    <rect 
                        x="-20" 
                        y={-thumbHeight / 2} 
                        width="40" 
                        height={thumbHeight} 
                        fill="#444" 
                        stroke="#222" 
                        strokeWidth="2" 
                        rx="4" 
                    />
                    <line x1="-15" y1="0" x2="15" y2="0" stroke="#fff" strokeWidth="3" />
                </g>
            </g>
        </svg>
    );
};
window.Fader = Fader;
