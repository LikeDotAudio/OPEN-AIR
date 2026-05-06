const LTPFader = ({ value, onChange, config }) => {
    // Parsing configuration from JSON
    const fConfig = config?.fader_config || {}; // Fader specific configs
    const kConfig = config?.knob_config || {}; // Knob specific configs for the cap
    const styleCfg = config?.style || {}; // General style overrides
    
    // Domain: Min/Max values for the fader
    const min = fConfig.value_min !== undefined ? fConfig.value_min : -60;
    const max = fConfig.value_max !== undefined ? fConfig.value_max : 12;
    const logExponent = fConfig.log_exponent || 1.0; // Logarithmic scale factor

    // Geometry: Determine orientation and dimensions
    const isHorizontal = config?.orientation === 'horizontal' || config?.layout?.W !== undefined;
    const height = config?.layout?.height || (isHorizontal ? 100 : 400);
    const width = config?.layout?.width || (isHorizontal ? 400 : 100);
    
    // Track Appearance
    const trackColor = styleCfg.tick_color || '#1a1a1a';
    
    // Current Value
    const faderVal = value !== undefined && value !== null ? value : (fConfig.value_default || min);

    // Interaction State
    const [isDragging, setIsDragging] = React.useState(false);
    const svgRef = React.useRef(null); // Ref for the SVG element

    // Pointer Event Handlers
    const handlePointerDown = (e) => {
        setIsDragging(true);
        updateValue(e);
        svgRef.current.setPointerCapture(e.pointerId);
    };

    const handlePointerMove = (e) => {
        if (isDragging) {
            updateValue(e);
        }
    };

    const handlePointerUp = (e) => {
        setIsDragging(false);
        svgRef.current.releasePointerCapture(e.pointerId);
    };

    const updateValue = (e) => {
        if (!svgRef.current) return;
        const svgRect = svgRef.current.getBoundingClientRect(); // Use SVG element's bounds
        
        let percent;
        if (isHorizontal) {
            const clientX = e.clientX;
            percent = (clientX - svgRect.left) / svgRect.width;
        } else {
            const clientY = e.clientY;
            percent = 1 - (clientY - svgRect.top) / svgRect.height; // Use svgRect for consistent bounds
        }
        
        percent = Math.max(0, Math.min(1, percent));
        
        // Logarithmic scale interpolation
        let norm = Math.pow(percent, logExponent);
        let newValue = min + norm * (max - min);
        newValue = Math.round(newValue * 100) / 100;
        onChange(newValue);
    };

    // Calculate Thumb Position based on value and scale
    const capRadius = kConfig.cap_radius || 22;
    const capColor = kConfig.cap_color || '#1a1a1a';
    const capOutline = kConfig.cap_outline_color || '#FF3131';

    const range = (max - min) || 1;
    const boundedValue = Math.max(min, Math.min(max, faderVal));
    let normForRender = (boundedValue - min) / range;
    if (logExponent !== 1.0) {
        normForRender = Math.pow(normForRender, 1.0 / logExponent);
    }
    
    const thumbPos = isHorizontal 
        ? normForRender * width
        : height - normForRender * height - capRadius; // Adjust for cap radius on vertical

    // Knob Shape Generator
    const renderShape = () => {
        const r = capRadius;
        const knobShape = styleCfg.knob_shape || 'circle';
        const gearTeeth = styleCfg.knob_teeth || 16;

        if (knobShape === 'gear') {
            const innerR = r * 0.85;
            const pts = [];
            for (let i = 0; i < gearTeeth * 4; i++) {
                const toothState = i % 4;
                const rad = (toothState === 1 || toothState === 2) ? r : innerR;
                const a = (i / (gearTeeth * 4)) * Math.PI * 2;
                pts.push(`${r * Math.cos(a)},${r * Math.sin(a)}`);
            }
            return <polygon points={pts.join(' ')} fill={`url(#ltp-grad-${config?.id || 'ltp'})`} stroke="#111" strokeWidth="1" />;
        } else if (knobShape === 'octagon') {
            const pts = [];
            for (let i = 0; i < 8; i++) {
                const a = (i / 8) * Math.PI * 2 + (Math.PI / 8);
                pts.push(`${r * Math.cos(a)},${r * Math.sin(a)}`);
            }
            return <polygon points={pts.join(' ')} fill={`url(#ltp-grad-${config?.id || 'ltp'})`} stroke="#111" strokeWidth="1" />;
        }
        return <circle cx="0" cy="0" r={r} fill={`url(#ltp-grad-${config?.id || 'ltp'})`} stroke="#111" strokeWidth="1" />;
    };

    // Pointer Generator
    const renderPointer = () => {
        const pLen = kConfig.pointer_length || (capRadius - 5);
        const pointerStyle = styleCfg.pointer_style || 'line';

        if (pointerStyle === 'dot') return <circle cx="0" cy={-pLen} r="3" fill="#fff" />;
        if (pointerStyle === 'triangle') return <polygon points={`0,${-pLen + 2} -5,${-pLen + 10} 5,${-pLen + 10}`} fill="#fff" />;
        if (pointerStyle === 'notch') return <rect x="-4" y={-capRadius} width="8" height="10" fill="#fff" rx="2" />;
        return <line x1="0" y1="0" x2="0" y2={-pLen} stroke="#fff" strokeWidth="2" strokeLinecap="round" />;
    };

    // Ticks for LTP fader
    const ticks = [];
    const tickInterval = fConfig?.tick_interval || ((max - min) / 10);
    const tickSteps = Math.abs(max - min) / tickInterval;
    const tickColorEffective = styleCfg.tick_color || trackColor;
    
    if (styleCfg.show_ticks !== false && tickInterval > 0 && tickSteps > 0) {
        for (let i = 0; i <= tickSteps; i++) {
            const tickVal = min + (i * tickInterval);
            let tNorm;
            if (logExponent !== 1.0) {
                let tRawNorm = (tickVal - min) / range;
                tNorm = Math.pow(tRawNorm, 1.0 / logExponent);
            } else {
                tNorm = (tickVal - min) / range;
            }

            if (isHorizontal) {
                const tickX = tNorm * width;
                ticks.push(<line key={i} x1={tickX} y1={height - 15} x2={tickX} y2={height - 5} stroke={tickColorEffective} strokeWidth="1" />);
            } else {
                const tickY = height - tNorm * height;
                const slotW = 10;
                const tickLen = width * 0.35;
                ticks.push(
                    <g key={i}>
                        <line x1={width/2 - tickLen} y1={tickY} x2={width/2 - slotW/2 - 2} y2={tickY} stroke={tickColorEffective} strokeWidth="1" />
                        <line x1={width/2 + slotW/2 + 2} y1={tickY} x2={width/2 + tickLen} y2={tickY} stroke={tickColorEffective} strokeWidth="1" />
                        {styleCfg.tick_label_position !== "left" && (
                            <text x={width/2 + tickLen + 8} y={tickY + 3} fill={tickColorEffective} fontSize="7" fontFamily="Arial">{tickVal}</text>
                        )}
                    </g>
                );
            }
        }
    }

    const faderValueDisplay = faderVal.toFixed(1);

    return (
        <div style={{ display: 'flex', flexDirection: isHorizontal ? 'row' : 'column', alignItems: 'center', gap: '10px' }}>
            <svg 
                ref={svgRef}
                width={isHorizontal ? width + capRadius : width} 
                height={isHorizontal ? height : height + capRadius} 
                style={{ touchAction: 'none', cursor: 'pointer', overflow: 'visible' }}
                onPointerDown={handlePointerDown}
                onPointerMove={handlePointerMove}
                onPointerUp={handlePointerUp}
                onPointerCancel={handlePointerUp}
            >
                <defs>
                    <linearGradient id={`ltp-grad-${config?.id || 'ltp'}`} x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stopColor="#666" />
                        <stop offset="30%" stopColor={capColor} />
                        <stop offset="100%" stopColor="#000" />
                    </linearGradient>
                    <filter id={`drop-shadow-ltp-${config?.id || 'ltp'}`} x="-20%" y="-20%" width="140%" height="140%">
                        <feDropShadow dx="2" dy="2" stdDeviation="2" floodColor="#000" floodOpacity="0.5"/>
                    </filter>
                </defs>

                <g>
                    {/* Track Slot */}
                    {isHorizontal ? (
                        <>
                            <rect x="0" y={height / 2 - 5} width={width} height="10" fill="#000" rx="5" stroke="#111" />
                            <rect x="0" y={height / 2 - 2} width={thumbPos} height="4" fill={trackColor} rx="2" />
                        </>
                    ) : (
                        <>
                            <rect x={width / 2 - 5} y="0" width="11" height={height} fill="#000" rx="5" stroke="#111" />
                            <rect x={width / 2 - 2} y={thumbPos} width="4" height={height - thumbPos} fill={trackColor} rx="2" />
                        </>
                    )}
                    
                    {ticks}

                    {/* The traveling Knob Cap */}
                    <g transform={isHorizontal ? `translate(${thumbPos}, ${height/2})` : `translate(${width / 2}, ${thumbPos})`}>
                        {renderShape()}
                        {/* Fake 3D inner ridge */}
                        <circle cx="0" cy="0" r={capRadius * 0.7} fill="#222" stroke="#111" />
                        {renderPointer()}
                    </g>
                </g>
            </svg>
            <div style={{ marginTop: '10px', fontFamily: 'monospace', fontSize: '12px', color: capOutline, backgroundColor: '#111', padding: '2px 8px', borderRadius: '4px', border: `1px solid ${capOutline}` }}>
                {faderValueDisplay} {fConfig.show_units && fConfig.unit_text}
            </div>
        </div>
    );
};
window.LTPFader = LTPFader;