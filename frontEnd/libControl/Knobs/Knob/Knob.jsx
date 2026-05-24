/**
 * Knob Architecture (Separated Concerns)
 * 1. KnobMotion: Logic for ranges, angles, and interaction.
 * 2. KnobTicks: Scale rendering (ticks and sizes).
 * 3. KnobCap: The 3D visual body (cap, shapes, glints).
 * 4. Main Orchestrator: Combines elements.
 */

// --- 1. MOTIONS & RANGES (Logic) ---
const getKnobAngles = (config, value, min, max) => {
    const knobStyle = (config?.cosmetics?.style_overrides?.knob_style || 
                      config?.cosmetics?.styling?.knob_style || 
                      config?.cosmetics?.visualization || 'standard').toLowerCase();

    const clamp = (val, min, max) => Math.max(min, Math.min(max, val));
    const boundedValue = clamp(value !== undefined && value !== null ? value : min, min, max);
    const norm = (boundedValue - min) / ((max - min) || 1);

    let startAngle = 240;
    let extent = -300;
    let pointerAngleDeg;

    if (knobStyle === 'panner') {
        startAngle = 90;
        extent = 135; 
        const mid = (min + max) / 2;
        const normFromCenter = (boundedValue - mid) / ((max - min) / 2 || 1);
        pointerAngleDeg = startAngle + (-normFromCenter * extent);
    } else if (knobStyle === 'dial') {
        startAngle = 90;
        extent = -360;
        pointerAngleDeg = startAngle + (norm * extent);
    } else {
        pointerAngleDeg = startAngle + (norm * extent);
    }

    return { startAngle, extent, pointerAngleDeg, norm };
};

// --- 2. TICK MARKS & SIZES ---
const KnobTicks = ({ center, radius, arcWidth, config, filterId, min = 0, max = 100 }) => {
    const scale = config?.cosmetics?.scale || config?.scale || {};
    const colors = config?.cosmetics?.colors || {};

    const showTicks = scale.show !== undefined ? scale.show : (config?.show_ticks || false);
    if (!showTicks) return null;

    // tick_style: 'simple' (lines), 'dots' (markers), 'numeric' (value labels).
    const tickStyle = (scale.style || config?.tick_style || 'simple').toLowerCase();
    const tickLength = scale.length !== undefined ? scale.length : (config?.tick_length || 10);
    const tickColor = colors.tick || colors.text || '#aaa';
    const tickCount = scale.count || 10;
    const tickThickness = scale.thickness || 1;

    const items = [];
    for (let i = 0; i <= tickCount; i++) {
        const ang = 240 - (i * (300 / tickCount));
        const rad = ang * Math.PI / 180;
        const r1 = radius + (arcWidth / 2) + 2;
        const r2 = r1 + tickLength;
        const ox = center + r1 * Math.cos(rad), oy = center - r1 * Math.sin(rad);
        const ex = center + r2 * Math.cos(rad), ey = center - r2 * Math.sin(rad);

        if (tickStyle === 'dots') {
            items.push(<circle key={i} cx={ex} cy={ey} r={Math.max(1, tickThickness + 1)} fill={tickColor} />);
        } else if (tickStyle === 'numeric') {
            const val = min + (i / tickCount) * (max - min);
            const label = Math.abs(val) >= 100 ? val.toFixed(0) : (Number.isInteger(val) ? String(val) : val.toFixed(1));
            const tr = r2 + 6;
            items.push(
                <text key={i} x={center + tr * Math.cos(rad)} y={center - tr * Math.sin(rad)}
                    fill={tickColor} fontSize="7" fontFamily="Arial" textAnchor="middle" alignmentBaseline="middle">
                    {label}
                </text>
            );
        } else {
            items.push(
                <line key={i} x1={ox} y1={oy} x2={ex} y2={ey} stroke={tickColor} strokeWidth={tickThickness} />
            );
        }
    }
    return <g className="knob-ticks">{items}</g>;
};

// --- 3. KNOB CAP (Visual Body) ---
const KnobCap = ({ center, radius, angle, config, filterId, indicatorColor }) => {
    const c = config || {};
    const cosmetics = c.cosmetics || {};
    const styling = cosmetics.styling || {};
    const overrides = cosmetics.style_overrides || {};
    const pointer = cosmetics.pointer || {};

    const knobStyle = (overrides.knob_style || styling.knob_style || cosmetics.visualization || c.knob_style || 'standard').toLowerCase();
    const defaultShape = knobStyle === 'gear' ? 'gear' : 'circle';
    const knobShape = (overrides.shape || styling.shape || c.shape || defaultShape).toLowerCase();
    
    const gearTeeth = styling.teeth || c.knob_teeth || 8;
    const outlineColor = styling.outline_color || c.knob_outline_color || '#444';
    const outlineThickness = styling.outline_thickness !== undefined ? styling.outline_thickness : (c.knob_outline_thickness || 0);
    const noCenter = styling.no_center || c.no_center || false;

    // Cap Scale logic: allow smaller caps to see ticks better (Default to 0.7 for better visibility)
    const capScale = styling.cap_scale !== undefined ? styling.cap_scale : 0.7;
    const capR = radius * capScale;

    const pointerStyle = (pointer.style || c.pointer_style || 'line').toLowerCase();
    // Default pointer length should reach near the track radius even if cap is small
    const pointerLength = pointer.length !== undefined ? pointer.length : (config?.pointer_length || (radius - 2));
    const pointerOffset = pointer.offset !== undefined ? pointer.offset : (config?.pointer_offset || 0);

    const DEPTH_OFFSET = 1.5;

    const renderGeometry = (r, fill, stroke, sWidth, rotation) => {
        const safeR = Math.max(0, r);
        if (knobShape === 'gear') {
            const innerR = safeR * 0.85; 
            const pts = [];
            for (let i = 0; i < gearTeeth * 4; i++) {
                const toothState = i % 4;
                const rad = (toothState === 1 || toothState === 2) ? safeR : innerR;
                const a = (i / (gearTeeth * 4)) * Math.PI * 2 + (rotation * Math.PI / 180);
                pts.push(`${center + rad * Math.cos(a)},${center - rad * Math.sin(a)}`);
            }
            return <polygon points={pts.join(' ')} fill={fill} stroke={stroke} strokeWidth={sWidth} />;
        } else if (knobShape === 'octagon') {
            const pts = [];
            for (let i = 0; i < 8; i++) {
                const a = (i / 8) * Math.PI * 2 + (Math.PI / 8) + (rotation * Math.PI / 180);
                pts.push(`${center + safeR * Math.cos(a)},${center - safeR * Math.sin(a)}`);
            }
            return <polygon points={pts.join(' ')} fill={fill} stroke={stroke} strokeWidth={sWidth} />;
        }
        return <circle cx={center} cy={center} r={safeR} fill={fill} stroke={stroke} strokeWidth={sWidth} />;
    };

    const renderPointer = (r, ang) => {
        const rad = ang * Math.PI / 180;
        const x1 = center + pointerOffset * Math.cos(rad);
        const y1 = center - pointerOffset * Math.sin(rad);
        const x2 = center + (pointerOffset + pointerLength) * Math.cos(rad);
        const y2 = center - (pointerOffset + pointerLength) * Math.sin(rad);

        if (pointerStyle === 'dot') {
            return <circle cx={x2} cy={y2} r="3" fill={indicatorColor} />;
        } else if (pointerStyle === 'triangle') {
            const triWidth = 5;
            const perp = rad + Math.PI / 2;
            const c1x = x1 + triWidth * Math.cos(perp);
            const c1y = y1 - triWidth * Math.sin(perp);
            const c2x = x1 - triWidth * Math.cos(perp);
            const c2y = y1 + triWidth * Math.sin(perp);
            return <polygon points={`${x2},${y2} ${c1x},${c1y} ${c2x},${c2y}`} fill={indicatorColor} />;
        } else if (pointerStyle === 'notch') {
            // Adjust notch length to reach pointerLength
            const nLen = 6;
            const nx1 = center + (pointerOffset + pointerLength - nLen) * Math.cos(rad);
            const ny1 = center - (pointerOffset + pointerLength - nLen) * Math.sin(rad);
            return <line x1={nx1} y1={ny1} x2={x2} y2={y2} stroke={indicatorColor} strokeWidth="4" strokeLinecap="butt" />;
        } else if (pointerStyle === 'thin') {
            return <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={indicatorColor} strokeWidth="1" strokeLinecap="round" />;
        } else if (pointerStyle === 'block') {
            return <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={indicatorColor} strokeWidth="6" strokeLinecap="butt" />;
        } else if (pointerStyle === 'tapered') {
            // Wedge: wide at the hub, point at the tip.
            const perp = rad + Math.PI / 2;
            const bh = 4;
            const bx1 = x1 + bh * Math.cos(perp), by1 = y1 - bh * Math.sin(perp);
            const bx2 = x1 - bh * Math.cos(perp), by2 = y1 + bh * Math.sin(perp);
            return <polygon points={`${x2},${y2} ${bx1},${by1} ${bx2},${by2}`} fill={indicatorColor} />;
        } else if (pointerStyle === 'vintage') {
            // Classic needle: tapered blade + counterweight tail + hub.
            const perp = rad + Math.PI / 2;
            const bh = 3.5;
            const bx1 = x1 + bh * Math.cos(perp), by1 = y1 - bh * Math.sin(perp);
            const bx2 = x1 - bh * Math.cos(perp), by2 = y1 + bh * Math.sin(perp);
            const tailLen = Math.max(6, pointerLength * 0.22);
            const tx = center - tailLen * Math.cos(rad), ty = center + tailLen * Math.sin(rad);
            return (
                <g>
                    <polygon points={`${x2},${y2} ${bx1},${by1} ${bx2},${by2}`} fill={indicatorColor} />
                    <line x1={center} y1={center} x2={tx} y2={ty} stroke={indicatorColor} strokeWidth="3" strokeLinecap="round" />
                    <circle cx={center} cy={center} r="3.5" fill={indicatorColor} />
                </g>
            );
        }
        return <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={indicatorColor} strokeWidth="2" strokeLinecap="round" />;
    };

    return (
        <g className="knob-cap-system">
            {/* 3D Body (Offset Base) */}
            <g transform={`translate(${DEPTH_OFFSET}, ${DEPTH_OFFSET})`}>
                {renderGeometry(capR, "#111", "none", 0, angle)}
            </g>

            {/* Top Cap (Offset NW) */}
            <g transform={`translate(${-DEPTH_OFFSET}, -${DEPTH_OFFSET})`} filter={`url(#sh-${filterId})`}>
                {renderGeometry(capR, `url(#grad-${filterId})`, outlineColor, outlineThickness, angle)}
                
                {/* 3D Effects: Glint & Inner Rim */}
                <g pointerEvents="none">
                    <circle cx={center + capR * 0.1} cy={center + capR * 0.1} r={capR * 0.9} fill="black" opacity="0.2" filter={`url(#blur-${filterId})`} />
                    <ellipse cx={center - capR * 0.4} cy={center - capR * 0.5} rx={capR * 0.6} ry={capR * 0.3} fill="white" opacity="0.3" filter={`url(#blur-${filterId})`} />
                    <path 
                        d={describeArc(center, center, capR - 3, 180, 270)} 
                        fill="none" stroke="white" strokeWidth="2" strokeOpacity="0.4" filter={`url(#blur-${filterId})`}
                    />
                </g>

                {!noCenter && <circle cx={center} cy={center} r={3} fill={indicatorColor} />}
                {renderPointer(capR, angle)}
            </g>
        </g>
    );
};

// --- 4. MAIN ORCHESTRATOR ---
const Knob = ({ value, onChange, config, size: defaultSize = 80 }) => {
    // 1. Config & Geometry Extraction
    const c = config || {};
    // Fluid: measure the rendered box and use a SQUARE measured size so the knob
    // redraws crisply at the resized scale while always staying round.
    const fluid = !!c.fluid;
    const wrapRef = React.useRef(null);
    const [measured, setMeasured] = React.useState(0);
    const cosmetics = c.cosmetics || {};
    const colors = cosmetics.colors || {};
    const styling = cosmetics.styling || {};
    
    const min = c.domain?.primary?.min !== undefined ? c.domain.primary.min : (c.min !== undefined ? c.min : 0);
    const max = c.domain?.primary?.max !== undefined ? c.domain.primary.max : (c.max !== undefined ? c.max : 100);
    
    const w = c.geometry?.width || c.width || defaultSize;
    const h = c.geometry?.height || c.height || defaultSize;
    const size = (fluid && measured) ? measured : Math.min(w, h);

    const arcWidth = styling.arc_width !== undefined ? styling.arc_width : (c.arc_width || 5);
    const indicatorColor = c.indicator_color || colors.active || colors.primary || '#33A1FD';
    const secondaryColor = colors.secondary || '#444444';
    const baseColor = styling.fill_color || c.knob_fill_color || '#333';

    const padding = (arcWidth / 2) + 12;
    const radius = ((size - (padding * 2)) / 2) * 0.8;
    const center = size / 2;

    // Fluid knobs measure their box (width) and redraw square at that size.
    React.useEffect(() => {
        if (!fluid || !wrapRef.current || typeof ResizeObserver === 'undefined') return;
        const ro = new ResizeObserver((entries) => {
            const wpx = Math.round(entries[0].contentRect.width);
            if (wpx > 0) setMeasured((p) => (p === wpx ? p : wpx));
        });
        ro.observe(wrapRef.current);
        return () => ro.disconnect();
    }, [fluid]);

    // 2. Interaction State
    const [isDragging, setIsDragging] = React.useState(false);
    const startYRef = React.useRef(0);
    const startValRef = React.useRef(0);

    const handlePointerDown = (e) => {
        setIsDragging(true);
        startYRef.current = e.clientY;
        startValRef.current = value !== undefined && value !== null ? value : min;
        e.target.setPointerCapture(e.pointerId);
    };

    const handlePointerMove = (e) => {
        if (!isDragging) return;
        const deltaY = startYRef.current - e.clientY;
        const range = max - min;
        const deltaVal = (deltaY / 150) * range; 
        onChange(Math.max(min, Math.min(max, Math.round((startValRef.current + deltaVal) * 100) / 100)));
    };

    const handlePointerUp = (e) => {
        setIsDragging(false);
        e.target.releasePointerCapture(e.pointerId);
    };

    // 3. Coordinate Sync
    const { startAngle, extent, pointerAngleDeg, norm } = getKnobAngles(c, value, min, max);
    const filterId = `knob-${c.id || Math.random().toString(36).substr(2, 9)}`;

    return (
        <div ref={wrapRef} style={{ width: fluid ? '100%' : size, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <svg
            width={size} height={size}
            viewBox={`0 0 ${size} ${size}`}
            style={{ touchAction: 'none', cursor: 'ns-resize', overflow: 'visible' }}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onPointerCancel={handlePointerUp}
        >
            <defs>
                <linearGradient id={`grad-${filterId}`} x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#555" />
                    <stop offset="30%" stopColor={baseColor} />
                    <stop offset="100%" stopColor="#111" />
                </linearGradient>
                <filter id={`sh-${filterId}`} x="-50%" y="-50%" width="200%" height="200%">
                    <feDropShadow dx="2" dy="2" stdDeviation="3" floodColor="#000" floodOpacity="0.6"/>
                </filter>
                <filter id={`blur-${filterId}`}>
                    <feGaussianBlur stdDeviation="2" />
                </filter>
            </defs>

            {/* Background Track / Indicator Arc */}
            <circle cx={center} cy={center} r={radius} fill="none" stroke={secondaryColor} strokeWidth={arcWidth} />
            <path 
                d={describeArc(center, center, radius, startAngle, startAngle + (norm * extent))} 
                fill="none" stroke={indicatorColor} strokeWidth={arcWidth} strokeLinecap="round"
            />

            {/* Ticks Component */}
            <KnobTicks center={center} radius={radius} arcWidth={arcWidth} config={c} filterId={filterId} min={min} max={max} />

            {/* Outer Bezel */}
            <circle cx={center} cy={center} r={radius + arcWidth/2 + 2} fill="none" stroke="#111" strokeWidth="1" />

            {/* Visual Cap Component */}
            <KnobCap 
                center={center} 
                radius={radius} 
                angle={pointerAngleDeg} 
                config={c} 
                filterId={filterId} 
                indicatorColor={indicatorColor}
            />
        </svg>
        </div>
    );
};

// --- HELPERS ---
function describeArc(x, y, radius, startAngle, endAngle) {
    const start = polarToCartesian(x, y, radius, endAngle);
    const end = polarToCartesian(x, y, radius, startAngle);
    const largeArcFlag = Math.abs(endAngle - startAngle) <= 180 ? "0" : "1";
    return ["M", start.x, start.y, "A", radius, radius, 0, largeArcFlag, 0, end.x, end.y].join(" ");
}

function polarToCartesian(centerX, centerY, radius, angleInDegrees) {
    const rad = angleInDegrees * Math.PI / 180.0;
    return { x: centerX + (radius * Math.cos(rad)), y: centerY - (radius * Math.sin(rad)) };
}

window.Knob = Knob;