const SelectorSwitch = ({ value, onChange, config }) => {
    // 1. Parsing Configuration
    const [lang] = window.useMqttLang();
    const title = config?.label?.[lang] || config?.label_active?.[lang] || config?.label?.En || config?.label_active?.En || "";
    const positions = config?.positions || ["OFF", "ON"];
    const isContinuous = config?.continuous === true;
    
    // Geometry & Layout
    const w = config?.width || config?.geometry?.width || config?.layout?.width || 120;
    const h = config?.height || config?.geometry?.height || config?.layout?.height || 140;
    const size = Math.min(w, h);
    
    // Cosmetics
    const baseColor = config?.knob_config?.cap_color || config?.cosmetics?.colors?.primary || '#333';
    const accentColor = config?.indicator_color || config?.cosmetics?.colors?.accent || '#0f0';
    const tickColor = config?.cosmetics?.colors?.text || '#888';
    
    const knobShape = config?.shape || config?.knob_shape || 'circle'; 
    const gearTeeth = config?.teeth || config?.knob_teeth || 16;
    const pointerStyle = config?.pointer_style || 'line';
    const noCenter = config?.no_center === true;

    // State Mapping
    let currentIndex = 0;
    if (typeof value === 'number') {
        currentIndex = value;
    } else if (typeof value === 'string') {
        const found = positions.indexOf(value);
        if (found !== -1) currentIndex = found;
    }

    const totalPos = positions.length;
    // Python match: continuous = 360/90, non-continuous = 300/240
    const sweepAngle = isContinuous ? 360 : 300;
    const startAngle = isContinuous ? 90 : 240; 
    const angleStep = sweepAngle / (isContinuous ? totalPos : Math.max(1, totalPos - 1));

    const eRef = React.useRef(null);
    const centerX = w / 2;
    const centerY = h / 2 - 10;
    const radius = size * 0.28;

    const getAngleForIndex = (idx) => {
        return startAngle - (idx * angleStep);
    };

    const updateFromPoint = (clientX, clientY) => {
        const rect = eRef.current.getBoundingClientRect();
        const cx = rect.left + rect.width / 2;
        const cy = rect.top + rect.height / 2 - 10;
        const dx = clientX - cx;
        const dy = clientY - cy;
        
        let angle = Math.atan2(-dy, dx) * (180 / Math.PI); // -dy because Y is down in browser
        if (angle < 0) angle += 360;
        
        // Map angle to index
        // startAngle is 240 (NW-ish). We want to find which position is closest
        let closestIdx = 0;
        let minDiff = Infinity;
        
        for(let i=0; i<totalPos; i++) {
            let targetAng = getAngleForIndex(i);
            while(targetAng < 0) targetAng += 360;
            while(targetAng >= 360) targetAng -= 360;
            
            let diff = Math.abs(angle - targetAng);
            if (diff > 180) diff = 360 - diff;
            
            if (diff < minDiff) {
                minDiff = diff;
                closestIdx = i;
            }
        }
        
        const finalVal = typeof positions[closestIdx] === 'string' ? positions[closestIdx] : closestIdx;
        onChange(finalVal);
    };

    const handlePointerDown = (e) => {
        e.target.setPointerCapture(e.pointerId);
        updateFromPoint(e.clientX, e.clientY);
    };

    // --- High Fidelity Renderers (Inherited from Knob.jsx) ---
    
    const renderShape = () => {
        const r = radius;
        if (knobShape === 'gear') {
            const innerR = r * 0.85;
            const pts = [];
            for (let i = 0; i < gearTeeth * 4; i++) {
                const toothState = i % 4;
                const rad = (toothState === 1 || toothState === 2) ? r : innerR;
                const a = (i / (gearTeeth * 4)) * Math.PI * 2;
                pts.push(`${rad * Math.cos(a)},${rad * Math.sin(a)}`);
            }
            return <polygon points={pts.join(' ')} fill={`url(#sel-grad-${config?.id})`} stroke="#000" strokeWidth="1" />;
        } else if (knobShape === 'octagon') {
            const pts = [];
            for (let i = 0; i < 8; i++) {
                const a = (i / 8) * Math.PI * 2 + (Math.PI / 8);
                pts.push(`${r * Math.cos(a)},${r * Math.sin(a)}`);
            }
            return <polygon points={pts.join(' ')} fill={`url(#sel-grad-${config?.id})`} stroke="#000" strokeWidth="1" />;
        }
        return <circle cx="0" cy="0" r={r} fill={`url(#sel-grad-${config?.id})`} stroke="#000" strokeWidth="1" />;
    };

    const renderPointer = () => {
        if (pointerStyle === 'dot') return <circle cx="0" cy={-radius + 6} r="3" fill={accentColor} />;
        if (pointerStyle === 'triangle') return <polygon points={`0,${-radius + 2} -5,${-radius + 12} 5,${-radius + 12}`} fill={accentColor} />;
        if (pointerStyle === 'notch') return <rect x="-4" y={-radius} width="8" height="10" fill={accentColor} rx="2" />;
        return <line x1="0" y1="0" x2="0" y2={-radius - 8} stroke={accentColor} strokeWidth="3" strokeLinecap="round" />;
    };

    const ticks = [];
    positions.forEach((p, i) => {
        const ang = getAngleForIndex(i);
        const rad = ang * Math.PI / 180;
        
        // Match Python: adj_cy - (radius + 2) * math.sin(angle_rad)
        const x1 = centerX + (radius + 5) * Math.cos(rad);
        const y1 = centerY - (radius + 5) * Math.sin(rad);
        const x2 = centerX + (radius + 14) * Math.cos(rad);
        const y2 = centerY - (radius + 14) * Math.sin(rad);
        
        const isActive = i === currentIndex;
        
        ticks.push(
            <g key={i}>
                <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={isActive ? accentColor : tickColor} strokeWidth={isActive ? 2 : 1} filter={isActive ? `url(#glow-sel-${config?.id})` : ''} />
                <text 
                    x={centerX + (radius + 32) * Math.cos(rad)} 
                    y={centerY - (radius + 32) * Math.sin(rad)} 
                    fill={isActive ? '#fff' : '#666'} 
                    fontSize="8" 
                    fontFamily="monospace" 
                    fontWeight={isActive ? "bold" : "normal"}
                    textAnchor="middle" 
                    dominantBaseline="middle"
                >
                    {p}
                </text>
            </g>
        );
    });

    const pointerAngleDeg = getAngleForIndex(currentIndex);

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <svg 
                ref={eRef}
                width={w} height={h} 
                style={{ touchAction: 'none', cursor: 'pointer', overflow: 'visible' }}
                onPointerDown={handlePointerDown}
            >
                <defs>
                    <linearGradient id={`sel-grad-${config?.id}`} x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stopColor="#666" />
                        <stop offset="30%" stopColor={baseColor} />
                        <stop offset="100%" stopColor="#000" />
                    </linearGradient>
                    <filter id={`shadow-sel-${config?.id}`}>
                        <feDropShadow dx="2" dy="2" stdDeviation="2" floodOpacity="0.5" />
                    </filter>
                    <filter id={`glow-sel-${config?.id}`}>
                        <feGaussianBlur stdDeviation="2" result="blur" />
                        <feComposite in="SourceGraphic" in2="blur" operator="over"/>
                    </filter>
                </defs>

                {/* Outer Rail / Bezel */}
                <circle cx={centerX} cy={centerY} r={radius + 4} fill="#111" />

                {ticks}

                {/* 3D Offset Base (Inherited from Knob.jsx) */}
                <g transform={`translate(${centerX + 1.5}, ${centerY + 1.5})`}>
                    {knobShape === 'circle' ? <circle cx="0" cy="0" r={radius} fill="#111" /> : null}
                </g>

                {/* The Main Cap (Inherited from Knob.jsx logic) */}
                <g transform={`translate(${centerX}, ${centerY}) rotate(${270 - pointerAngleDeg})`} filter={`url(#shadow-sel-${config?.id})`}>
                    {renderShape()}
                    
                    {/* Inner Center Ridge */}
                    {!noCenter && <circle cx="0" cy="0" r={radius * 0.5} fill="#1a1a1a" stroke="#000" strokeWidth="1" />}
                    
                    {renderPointer()}
                </g>

                {/* Glint & Dome Overlays (Inherited from Knob.jsx) */}
                <g transform={`translate(${centerX}, ${centerY})`} pointerEvents="none">
                    <ellipse cx={-radius * 0.4} cy={-radius * 0.5} rx={radius * 0.6} ry={radius * 0.3} fill="rgba(255,255,255,0.15)" filter="blur(2px)" />
                </g>

                {/* Title */}
                {title && (
                    <text x={centerX} y={h - 10} fill="#aaa" fontSize="10" fontWeight="bold" textAnchor="middle">{title.toUpperCase()}</text>
                )}
            </svg>
        </div>
    );
};
window.SelectorSwitch = SelectorSwitch;