const Knob = ({ value, onChange, config, size: defaultSize = 80 }) => {
    // Dynamic Config Parsing
    const min = config?.domain?.primary?.min !== undefined ? config.domain.primary.min : 0;
    const max = config?.domain?.primary?.max !== undefined ? config.domain.primary.max : 100;
    const logExponent = config?.domain?.primary?.log_exponent || 1.0;
    
    // Geometry
    const w = config?.geometry?.width || config?.layout?.width || config?.width || defaultSize;
    const h = config?.geometry?.height || config?.layout?.height || config?.height || defaultSize;
    const size = Math.min(w, h);
    
    // Cosmetics & Styling
    const baseColor = config?.knob_config?.cap_color || config?.cosmetics?.colors?.primary || config?.base_color || '#333';
    const accentColor = config?.knob_config?.cap_outline_color || config?.indicator_color || config?.cosmetics?.colors?.accent || '#33A1FD';
    const tickColor = config?.style?.tick_color || config?.cosmetics?.colors?.text || '#aaa';
    const bgColor = config?.cosmetics?.colors?.background || config?.bg_color || '#2b2b2b';
    
    const knobStyle = config?.style?.knob_style || config?.knob_style || 'standard'; // 'standard', 'panner', 'dial'
    const knobShape = config?.style?.knob_shape || config?.shape || (knobStyle === 'gear' ? 'gear' : 'circle'); // 'circle', 'octagon', 'gear'
    const gearTeeth = config?.style?.knob_teeth || config?.teeth || 16;
    const pointerStyle = config?.style?.pointer_style || config?.pointer_style || 'line'; // 'line', 'dot', 'triangle', 'notch'
    
    const showTicks = config?.style?.show_ticks !== false;
    const tickStyle = config?.style?.tick_style || config?.tick_style || 'line'; // 'line', 'dots', 'numeric'
    const tickLength = config?.style?.tick_length || config?.tick_length || 10;
    const arcWidth = config?.style?.arc_width || config?.arc_width || 5;

    const showLabel = config?.readout?.show_label !== false;
    const textInside = config?.readout?.text_inside === true;
    const textPos = config?.readout?.label_position || 'top';
    const noCenter = config?.style?.no_center === true;

    // Angle limits for knob sweep
    const minAngle = config?.geometry?.min_angle !== undefined ? config.geometry.min_angle : config?.min_angle !== undefined ? config.min_angle : -135;
    const maxAngle = config?.geometry?.max_angle !== undefined ? config.geometry.max_angle : config?.max_angle !== undefined ? config.max_angle : 135;
    
    // State for dragging
    const [isDragging, setIsDragging] = React.useState(false);
    const svgRef = React.useRef(null); // Ref for the SVG element
    const startYRef = React.useRef(0);
    const startValRef = React.useRef(0);

    const clamp = (val, min, max) => Math.max(min, Math.min(max, val));

    const handlePointerDown = (e) => {
        setIsDragging(true);
        startYRef.current = e.clientY;
        startValRef.current = value !== undefined && value !== null ? value : min;
        e.target.setPointerCapture(e.pointerId);
    };

    const handlePointerMove = (e) => {
        if (!isDragging) return;
        const deltaY = startYRef.current - e.clientY;
        // Sensitivity: 1 pixel = 1 unit (scaled by range)
        const range = max - min;
        const deltaVal = (deltaY / 100) * range; 
        const newVal = clamp(startValRef.current + deltaVal, min, max);
        onChange(Math.round(newVal * 100) / 100);
    };

    const handlePointerUp = (e) => {
        setIsDragging(false);
        e.target.releasePointerCapture(e.pointerId);
    };

    // Calculate current angle based on value
    const boundedValue = clamp(value !== undefined && value !== null ? value : min, min, max);
    const percentage = (boundedValue - min) / ((max - min) || 1);
    const angle = minAngle + percentage * (maxAngle - minAngle);

    const radius = size / 2;
    const center = size / 2;

    // Helper to render different knob shapes
    const renderShape = () => {
        const r = radius - 10; // Radius for the main shape, slightly smaller than SVG radius
        if (knobShape === 'gear') {
            const innerR = r * 0.85;
            const pts = [];
            for (let i = 0; i < gearTeeth * 4; i++) {
                const toothState = i % 4;
                const currentR = (toothState === 1 || toothState === 2) ? r : innerR;
                const a = (i / (gearTeeth * 4)) * Math.PI * 2;
                pts.push(`${center + currentR * Math.cos(a)},${center + currentR * Math.sin(a)}`);
            }
            return <polygon points={pts.join(' ')} fill={`url(#knob-grad-${config?.id || 'knob'})`} stroke="#111" strokeWidth="2" />;
        } else if (knobShape === 'octagon') {
            const pts = [];
            for (let i = 0; i < 8; i++) {
                const a = (i / 8) * Math.PI * 2 + (Math.PI / 8);
                pts.push(`${center + r * Math.cos(a)},${center + r * Math.sin(a)}`);
            }
            return <polygon points={pts.join(' ')} fill={`url(#knob-grad-${config?.id || 'knob'})`} stroke="#111" strokeWidth="2" />;
        } else { // Default to circle
            return <circle cx={center} cy={center} r={r} fill={`url(#knob-grad-${config?.id || 'knob'})`} stroke="#111" strokeWidth="2" />;
        }
    };

    // Helper to render different pointer styles
    const renderPointer = () => {
        const pLen = config?.pointer_length || (radius - 15);
        if (pointerStyle === 'dot') {
            return <circle cx={center} cy={center - radius + 6} r="3" fill={accentColor} />;
        } else if (pointerStyle === 'triangle') {
            return <polygon points={`${center},${center - radius + 2} ${center - 5},${center - radius + 12} ${center + 5},${center - radius + 12}`} fill={accentColor} />;
        } else if (pointerStyle === 'notch') {
            return <rect x={center - 4} y={center - radius} width="8" height="10" fill={accentColor} rx="2" />;
        } else { // Default to line
            return <line x1={center} y1={center} x2={center} y2={center - pLen} stroke={accentColor} strokeWidth="3" strokeLinecap="round" />;
        }
    };

    return (
        <svg 
            ref={svgRef} // Attach ref to SVG for interaction bounds
            width={size} 
            height={size} 
            style={{ touchAction: 'none', cursor: 'ns-resize' }} // Cursor style adjusted for vertical drag
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onPointerCancel={handlePointerUp}
        >
            <defs>
                <linearGradient id={`knob-grad-${config?.id || 'knob'})`} x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#555" />
                    <stop offset="30%" stopColor={baseColor} />
                    <stop offset="100%" stopColor="#111" />
                </linearGradient>
                <filter id={`drop-shadow-knob-${config?.id || 'knob'})`} x="-20%" y="-20%" width="140%" height="140%">
                    <feDropShadow dx="2" dy="2" stdDeviation="2" floodColor="#000" floodOpacity="0.5"/>
                </filter>
                <filter id={`glow-${config?.id || 'knob'})`} x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="3" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over"/>
                </filter>
            </defs>

            {/* Outer Bezel Shadow Ring */}
            <circle cx={center} cy={center} r={radius + 10} fill="#111" />
            
            {/* Ticks/Scale indicator */}
            <circle 
                cx={center} 
                cy={center} 
                r={radius + 5} 
                fill="none" 
                stroke={tickColor} 
                strokeWidth="2" 
                strokeDasharray="4 6" 
            />

            {/* Rotating Core Group */}
            <g transform={`rotate(${angle}, ${center}, ${center})`} filter={`url(#drop-shadow-knob-${config?.id || 'knob'})`}>
                {renderShape()}
                
                {/* 3D Convex Dome simulation */}
                <circle cx={center} cy={center} r={radius - 2} fill="url(#knob-grad-overlay)" opacity="0.3" />
                <radialGradient id="knob-grad-overlay" cx="30%" cy="30%" r="70%">
                    <stop offset="0%" stopColor="#fff" stopOpacity="0.4" />
                    <stop offset="100%" stopColor="#000" stopOpacity="0.8" />
                </radialGradient>

                {/* Inner Indent */}
                {!noCenter && <circle cx={center} cy={center} r={radius * 0.5} fill="#1a1a1a" stroke="#000" strokeWidth="1" />}
                
                {renderPointer()}
            </g>
        </svg>
    );
};
window.Knob = Knob;