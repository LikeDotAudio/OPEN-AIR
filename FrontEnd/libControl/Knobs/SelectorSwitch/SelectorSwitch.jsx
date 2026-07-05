/**
 * Header: SelectorSwitch.jsx
 * Purpose: SelectorSwitch component or utility.
 * Description: Handles logic and rendering for SelectorSwitch component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// Inline comment: Logic for SelectorSwitch
const SelectorSwitch = ({ value, onChange, config }) => {
    // --- 1. Robust Config Extraction (Mirroring Python's knob_config.py) ---
    const c = config || {};
    const cosmetics = c.cosmetics || {};
    const styling = cosmetics.styling || {};
    const overrides = cosmetics.style_overrides || {};
    const pointer = cosmetics.pointer || {};
    const colors = cosmetics.colors || {};

    const [lang] = window.useMqttLang();
    const title = c.label?.[lang] || c.label_active?.[lang] || c.label?.En || c.label_active?.En || "";
    const positions = c.positions || ["OFF", "ON"];
    const isContinuous = c.continuous === true;

    // Colors
    const accentColor = colors.primary || '#33A1FD';
    const secondaryColor = colors.secondary || '#444444';
    const indicatorColor = c.indicator_color || colors.active || accentColor;
    const tickColor = colors.text || '#888';
    
    // Geometry
    const w = config?.width || config?.geometry?.width || config?.layout?.width || 120;
    const h = config?.height || config?.geometry?.height || config?.layout?.height || 140;
    const size = Math.min(w, h);

    // Aesthetics
    const knobStyle = (overrides.knob_style || styling.knob_style || cosmetics.visualization || c.knob_style || 'standard').toLowerCase();
    const defaultShape = knobStyle === 'gear' ? 'gear' : 'circle';
    const knobShape = (overrides.shape || styling.shape || c.shape || defaultShape).toLowerCase();
    
    const baseColor = styling.fill_color || c.knob_fill_color || '#333';
    const outlineColor = styling.outline_color || c.knob_outline_color || secondaryColor;
    const gearTeeth = styling.teeth || c.knob_teeth || 8;
    const noCenter = styling.no_center || c.no_center || false;

    // Pointer
    const pointerStyle = (pointer.style || c.pointer_style || 'line').toLowerCase();

    // --- 2. State Mapping & Layout Math ---
    let currentIndex = 0;
    if (typeof value === 'number') {
        currentIndex = value;
    } else if (typeof value === 'string') {
        const found = positions.indexOf(value);
        if (found !== -1) currentIndex = found;
    }

    const totalPos = positions.length;
    // Python: (90, 360) if continuous else (240, 300)
    const sweepAngle = isContinuous ? 360 : 300;
    const startAngle = isContinuous ? 90 : 240; 
    const angleStep = sweepAngle / (isContinuous ? totalPos : Math.max(1, totalPos - 1));

    const eRef = React.useRef(null);
    const centerX = w / 2;
    const centerY = h / 2;
    
    // Python Layout: adj_cy = cy + (top_res - bottom_res) / 2
    const topRes = title ? 20 : 0;
    const bottomRes = 20;
    const adjCy = centerY + (topRes - bottomRes) / 2;
    const radius = Math.min(w, h - topRes - bottomRes) / 2 - 25;

    const getAngleForIndex = (idx) => {
        return startAngle - (idx * angleStep);
    };

    const updateFromPoint = (clientX, clientY) => {
        const rect = eRef.current.getBoundingClientRect();
        const cx = rect.left + rect.width / 2;
        const cy = rect.top + adjCy;
        const dx = clientX - cx;
        const dy = clientY - cy;
        
        let angle = Math.atan2(-dy, dx) * (180 / Math.PI); 
        if (angle < 0) angle += 360;
        
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

    // Mouse wheel steps to the next/previous position. Continuous selectors wrap
    // around; discrete ones clamp at the ends. Scroll up = next position.
    // Uses a NON-PASSIVE native listener (see Knob.jsx) so preventDefault() stops
    // a scrollable ancestor from eating the wheel; the latest handler is held in
    // a ref so the once-attached listener sees the current index/positions.
    const wheelRef = React.useRef(null);
    wheelRef.current = (e) => {
        const dir = e.deltaY < 0 ? 1 : -1;
        let next = currentIndex + dir;
        if (isContinuous) next = (next + totalPos) % totalPos;
        else next = Math.max(0, Math.min(totalPos - 1, next));
        onChange(typeof positions[next] === 'string' ? positions[next] : next);
    };
    React.useEffect(() => {
        const el = eRef.current;
        if (!el) return;
        const onWheel = (e) => { e.preventDefault(); wheelRef.current && wheelRef.current(e); };
        el.addEventListener('wheel', onWheel, { passive: false });
        return () => el.removeEventListener('wheel', onWheel);
    }, []);

    const renderShape = (r, fill, stroke, sWidth, rotation = 0) => {
        if (knobShape === 'gear') {
            const innerR = r * 0.85; 
            const pts = [];
            const teeth = gearTeeth;
            for (let i = 0; i < teeth * 4; i++) {
                const toothState = i % 4;
                const rad = (toothState === 1 || toothState === 2) ? r : innerR;
                const a = (i / (teeth * 4)) * Math.PI * 2 + (rotation * Math.PI / 180);
                pts.push(`${rad * Math.cos(a)},${-rad * Math.sin(a)}`);
            }
            return <polygon points={pts.join(' ')} fill={fill} stroke={stroke} strokeWidth={sWidth} />;
        } else if (knobShape === 'octagon') {
            const pts = [];
            for (let i = 0; i < 8; i++) {
                const a = (i / 8) * Math.PI * 2 + (Math.PI / 8) + (rotation * Math.PI / 180);
                pts.push(`${r * Math.cos(a)},${-r * Math.sin(a)}`);
            }
            return <polygon points={pts.join(' ')} fill={fill} stroke={stroke} strokeWidth={sWidth} />;
        }
        return <circle cx="0" cy="0" r={Math.max(0, r)} fill={fill} stroke={stroke} strokeWidth={sWidth} />;
    };

    const renderPointer = (r, angle) => {
        const rad = angle * Math.PI / 180;
        // Python: pointer length is radius + 14 (extends past knob to ticks)
        const pLen = r + 14; 
        const x2 = pLen * Math.cos(rad);
        const y2 = -pLen * Math.sin(rad);

        if (pointerStyle === 'dot') return <circle cx={x2} cy={y2} r="3" fill={indicatorColor} />;
        if (pointerStyle === 'triangle') {
            const triWidth = 5;
            const perp = rad + Math.PI / 2;
            const c1x = 0 + triWidth * Math.cos(perp);
            const c1y = 0 - triWidth * Math.sin(perp);
            const c2x = 0 - triWidth * Math.cos(perp);
            const c2y = 0 + triWidth * Math.sin(perp);
            return <polygon points={`${x2},${y2} ${c1x},${c1y} ${c2x},${c2y}`} fill={indicatorColor} />;
        }
        if (pointerStyle === 'notch') return <line x1={0} y1={0} x2={x2} y2={y2} stroke={indicatorColor} strokeWidth="4" strokeLinecap="butt" />;
        return <line x1="0" y1="0" x2={x2} y2={y2} stroke={indicatorColor} strokeWidth="3" strokeLinecap="round" />;
    };

    // NOTE: filterId MUST be declared before the ticks loop uses it — otherwise it
    // is a temporal-dead-zone ReferenceError that crashes the whole component
    // (the rotary selector renders blank / "doesn't work").
    const filterId = `sel-${c.id || Math.random().toString(36).substr(2, 9)}`;
    const ticks = [];
    positions.forEach((p, i) => {
        const ang = getAngleForIndex(i);
        const rad = ang * Math.PI / 180;
        // Python: ts_x = cx + (radius + 2), te_x = cx + (radius + 10), tl_x = cx + (radius + 24)
        const x1 = (radius + 2) * Math.cos(rad);
        const y1 = -(radius + 2) * Math.sin(rad);
        const x2 = (radius + 10) * Math.cos(rad);
        const y2 = -(radius + 10) * Math.sin(rad);
        const tlX = (radius + 24) * Math.cos(rad);
        const tlY = -(radius + 24) * Math.sin(rad);
        
        const isActive = i === currentIndex;
        
        ticks.push(
            <g key={i}>
                <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={isActive ? indicatorColor : tickColor} strokeWidth={isActive ? 2 : 1} filter={isActive ? `url(#glow-${filterId})` : ''} />
                <text 
                    x={tlX} 
                    y={tlY} 
                    fill={isActive ? indicatorColor : '#666'} 
                    fontSize="8" 
                    fontFamily="Helvetica, Arial, sans-serif" 
                    fontWeight={isActive ? "bold" : "normal"}
                    textAnchor="middle" 
                    dominantBaseline="middle"
                >
                    {p}
                </text>
            </g>
        );
    });

    const DEPTH_OFFSET = 1.5;
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
                    <linearGradient id={`grad-${filterId}`} x1="0%" y1="0%" x2="0%" y2="100%">
                        {/* Softer shading (matches Knob): gentle top highlight, lifted bottom. */}
                        <stop offset="0%" stopColor="#484848" />
                        <stop offset="50%" stopColor={baseColor} />
                        <stop offset="100%" stopColor="#1e1e1e" />
                    </linearGradient>
                    <filter id={`sh-${filterId}`} x="-50%" y="-50%" width="200%" height="200%">
                        <feDropShadow dx="2" dy="2" stdDeviation="3" floodColor="#000" floodOpacity="0.6"/>
                    </filter>
                    <filter id={`glow-${filterId}`}>
                        <feGaussianBlur stdDeviation="2" result="blur" />
                        <feComposite in="SourceGraphic" in2="blur" operator="over"/>
                    </filter>
                    <filter id={`blur-${filterId}`}>
                        <feGaussianBlur stdDeviation="2" />
                    </filter>
                </defs>

                {/* Title (n-anchor, top 10) */}
                {title && (
                    <text x={centerX} y={10} fill="#fff" fontSize="9" fontWeight="bold" textAnchor="middle" dominantBaseline="hanging">{title.toUpperCase()}</text>
                )}

                <g transform={`translate(${centerX}, ${adjCy})`}>
                    {/* Outer Bezel / Track */}
                    {isContinuous ? (
                        <circle cx="0" cy="0" r={Math.max(0, radius)} fill="none" stroke={secondaryColor} strokeWidth="2" />
                    ) : (
                        <path 
                            d={describeArc(0, 0, radius, startAngle, startAngle - sweepAngle)} 
                            fill="none" stroke={secondaryColor} strokeWidth="2"
                        />
                    )}

                    {ticks}

                    {/* 3D Body (Offset Base) */}
                    <g transform={`translate(${DEPTH_OFFSET}, ${DEPTH_OFFSET})`}>
                        {renderShape(radius - 5, "#111", "none", 0, pointerAngleDeg)}
                    </g>

                    {/* The Main Cap (Offset NW) */}
                    <g transform={`translate(${-DEPTH_OFFSET}, ${-DEPTH_OFFSET})`} filter={`url(#sh-${filterId})`}>
                        {renderShape(radius - 5, `url(#grad-${filterId})`, outlineColor, 1, pointerAngleDeg)}
                        
                        {/* 3D Effects: Glint & Inner Rim — clipped to the cap shape so
                            the reflection/blur never spills past the cap edge, and
                            toned down (softer, less intense) to match the Knob. */}
                        <clipPath id={`capclip-${filterId}`}>
                            {renderShape(radius - 5, "#fff", "none", 0, pointerAngleDeg)}
                        </clipPath>
                        <g pointerEvents="none" clipPath={`url(#capclip-${filterId})`}>
                            <circle cx={(radius-5) * 0.1} cy={(radius-5) * 0.1} r={Math.max(0, (radius-5) * 0.9)} fill="black" opacity="0.15" filter={`url(#blur-${filterId})`} />
                            <ellipse cx={-(radius-5) * 0.4} cy={-(radius-5) * 0.5} rx={Math.max(0, (radius-5) * 0.55)} ry={Math.max(0, (radius-5) * 0.28)} fill="white" opacity="0.13" filter={`url(#blur-${filterId})`} />
                            <path
                                d={describeArc(0, 0, (radius-5) - 3, 180, 270)}
                                fill="none" stroke="white" strokeWidth="2" strokeOpacity="0.22" filter={`url(#blur-${filterId})`}
                            />
                        </g>

                        {!noCenter && <circle cx="0" cy="0" r={3} fill={indicatorColor} />}
                        {renderPointer(radius - 5, pointerAngleDeg)}
                    </g>
                </g>

                {/* Selection Text (s-anchor, bottom 10) */}
                {positions[currentIndex] !== undefined && (
                    <text x={centerX} y={h - 10} fill={indicatorColor} fontSize="9" fontWeight="bold" textAnchor="middle">{positions[currentIndex].toString().toUpperCase()}</text>
                )}
            </svg>
        </div>
    );
};

// Inline comment: Logic for describeArc
function describeArc(x, y, radius, startAngle, endAngle) {
    const start = polarToCartesian(x, y, radius, endAngle);
    const end = polarToCartesian(x, y, radius, startAngle);
    // Note: for SelectorSwitch, sweep is CW in SVG (downward), but startAngle is CCW (standard math).
    // Large arc flag needs adjustment if sweep > 180
    const largeArcFlag = Math.abs(endAngle - startAngle) <= 180 ? "0" : "1";
    // We want the arc to follow CCW order (start -> end)
    return ["M", start.x, start.y, "A", radius, radius, 0, largeArcFlag, 0, end.x, end.y].join(" ");
}

// Inline comment: Logic for polarToCartesian
function polarToCartesian(centerX, centerY, radius, angleInDegrees) {
    const rad = angleInDegrees * Math.PI / 180.0;
    return { x: centerX + (radius * Math.cos(rad)), y: centerY - (radius * Math.sin(rad)) };
}

window.SelectorSwitch = SelectorSwitch;