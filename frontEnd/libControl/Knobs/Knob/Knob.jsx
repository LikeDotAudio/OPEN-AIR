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
    // If the style name IS a shape (gear/octagon/circle), use it as the default
    // cap shape so `visualization:"octagon"` actually renders as an octagon
    // without needing an explicit style_overrides.shape.
    const defaultShape = (knobStyle === 'gear' || knobStyle === 'octagon' || knobStyle === 'circle')
        ? knobStyle : 'circle';
    const knobShape = (overrides.shape || styling.shape || c.shape || defaultShape).toLowerCase();
    const isChicken = knobStyle === 'chicken' || knobShape === 'chicken';
    const isMarconi = knobStyle === 'marconi' || knobShape === 'marconi';
    const colors = cosmetics.colors || {};

    const gearTeeth = styling.teeth || c.knob_teeth || 8;
    const outlineColor = styling.outline_color || c.knob_outline_color || '#444';
    const outlineThickness = styling.outline_thickness !== undefined ? styling.outline_thickness : (c.knob_outline_thickness || 0);
    const noCenter = styling.no_center || c.no_center || false;

    // Cap Scale logic: allow smaller caps to see ticks better (Default to 0.7 for better visibility)
    const capScale = styling.cap_scale !== undefined ? styling.cap_scale : 0.7;
    const capR = radius * capScale;

    const pointerStyle = (pointer.style || c.pointer_style || 'line').toLowerCase();
    // length may be null (the schema's "reach the track" sentinel). Use != null so
    // null falls through to the default instead of coercing to a 0-length pointer.
    const pointerLength = (pointer.length != null) ? pointer.length
        : ((config?.pointer_length != null) ? config.pointer_length : (radius - 2));
    const pointerOffset = (pointer.offset != null) ? pointer.offset
        : ((config?.pointer_offset != null) ? config.pointer_offset : 0);

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

    // --- CHICKEN-HEAD cap: round body + tapered "beak" pointer on a skirt. The
    // beak IS the indicator (no separate pointer). Colour-aware glossy gradient. ---
    if (isChicken) {
        const body = styling.fill_color || colors.primary || indicatorColor || '#cccccc';
        const gTop = shadeHex(body, 0.32), gBot = shadeHex(body, -0.45), ridge = shadeHex(body, -0.5);
        // Chicken-head: long tapered BEAK forward + short blunt "bum" tail back,
        // widest at the centre hub (per the Q-parts top view).
        const bodyR = radius * 0.40, skirtR = radius * 0.52;
        const rad = angle * Math.PI / 180;
        const P = (d, cc) => `${center + d * Math.cos(rad) - cc * Math.sin(rad)},${center - d * Math.sin(rad) - cc * Math.cos(rad)}`;
        const tipLen = radius * 1.02, bumLen = radius * 0.70;
        const hw = bodyR * 1.05, hwBum = hw * 0.5;
        const beak = [P(tipLen, 0), P(0, hw), P(-bumLen, hwBum), P(-bumLen, -hwBum), P(0, -hw)].join(' ');
        const tx = center + tipLen * Math.cos(rad), ty = center - tipLen * Math.sin(rad);
        return (
            <g className="knob-cap-system chicken">
                <defs>
                    <linearGradient id={`chgrad-${filterId}`} x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stopColor={gTop} /><stop offset="55%" stopColor={body} /><stop offset="100%" stopColor={gBot} />
                    </linearGradient>
                </defs>
                <circle cx={center} cy={center} r={skirtR} fill={shadeHex(body, -0.55)} stroke="#000" strokeWidth="1" filter={`url(#sh-${filterId})`} opacity="0.95" />
                <g transform={`translate(${DEPTH_OFFSET}, ${DEPTH_OFFSET})`}>
                    <polygon points={beak} fill="#0b0b0b" strokeLinejoin="round" />
                    <circle cx={center} cy={center} r={bodyR} fill="#0b0b0b" />
                </g>
                <g transform={`translate(${-DEPTH_OFFSET}, -${DEPTH_OFFSET})`} filter={`url(#sh-${filterId})`}>
                    <polygon points={beak} fill={`url(#chgrad-${filterId})`} stroke={outlineColor} strokeWidth={outlineThickness} strokeLinejoin="round" />
                    <circle cx={center} cy={center} r={bodyR} fill={`url(#chgrad-${filterId})`} stroke={outlineColor} strokeWidth={outlineThickness} />
                    <clipPath id={`capclip-${filterId}`}><polygon points={beak} /><circle cx={center} cy={center} r={bodyR} /></clipPath>
                    <g pointerEvents="none" clipPath={`url(#capclip-${filterId})`}>
                        <ellipse cx={center - bodyR * 0.32} cy={center - bodyR * 0.4} rx={bodyR * 0.55} ry={bodyR * 0.28} fill="white" opacity="0.16" filter={`url(#blur-${filterId})`} />
                        <circle cx={center + bodyR * 0.1} cy={center + bodyR * 0.15} r={bodyR * 0.85} fill="black" opacity="0.12" filter={`url(#blur-${filterId})`} />
                    </g>
                    <line x1={center} y1={center} x2={tx} y2={ty} stroke={ridge} strokeWidth="1.5" strokeLinecap="round" opacity="0.6" />
                </g>
            </g>
        );
    }

    // --- MARCONI ("Elma" British wing) cap: cylinder body + blunt wing fin with a
    // white indicator line, on a metallic skirt. ---
    if (isMarconi) {
        const body = styling.fill_color || colors.primary || indicatorColor || '#9aa3ad';
        const gTop = shadeHex(body, 0.30), gBot = shadeHex(body, -0.42);
        // ONE solid rectangular wing that passes THROUGH the body: protrudes the
        // same distance on BOTH sides (pointer side and opposite side). Only the
        // pointer side gets the white indicator line; the opposite side is bare.
        const bodyR = radius * 0.62, skirtR = radius * 0.93;
        const rad = angle * Math.PI / 180;
        const P = (d, cc) => `${center + d * Math.cos(rad) - cc * Math.sin(rad)},${center - d * Math.sin(rad) - cc * Math.cos(rad)}`;
        const wingLen = radius * 1.02;
        const wH = bodyR * 0.50;
        const wing = [P(-wingLen, wH), P(wingLen, wH), P(wingLen, -wH), P(-wingLen, -wH)].join(' ');
        const lx1 = center + bodyR * 0.40 * Math.cos(rad), ly1 = center - bodyR * 0.40 * Math.sin(rad);
        const lx2 = center + (wingLen - 1) * Math.cos(rad), ly2 = center - (wingLen - 1) * Math.sin(rad);
        const lineW = Math.max(2, radius * 0.045);
        return (
            <g className="knob-cap-system marconi">
                <defs>
                    <linearGradient id={`mcgrad-${filterId}`} x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stopColor={gTop} /><stop offset="55%" stopColor={body} /><stop offset="100%" stopColor={gBot} />
                    </linearGradient>
                    <radialGradient id={`mcskirt-${filterId}`} cx="40%" cy="35%" r="75%">
                        <stop offset="0%" stopColor="#f2f2f2" /><stop offset="55%" stopColor="#b8bcc0" /><stop offset="100%" stopColor="#6e7378" />
                    </radialGradient>
                </defs>
                <circle cx={center} cy={center} r={skirtR} fill={`url(#mcskirt-${filterId})`} stroke="#5a5e63" strokeWidth="1" filter={`url(#sh-${filterId})`} />
                <circle cx={center} cy={center} r={skirtR} fill="none" stroke="#ffffff" strokeWidth="1" opacity="0.35" />
                <g transform={`translate(${DEPTH_OFFSET}, ${DEPTH_OFFSET})`}>
                    <polygon points={wing} fill="#0b0b0b" strokeLinejoin="round" />
                    <circle cx={center} cy={center} r={bodyR} fill="#0b0b0b" />
                </g>
                <g transform={`translate(${-DEPTH_OFFSET}, -${DEPTH_OFFSET})`} filter={`url(#sh-${filterId})`}>
                    <polygon points={wing} fill={`url(#mcgrad-${filterId})`} stroke={outlineColor} strokeWidth={outlineThickness} strokeLinejoin="round" />
                    <circle cx={center} cy={center} r={bodyR} fill={`url(#mcgrad-${filterId})`} stroke={outlineColor} strokeWidth={outlineThickness} />
                    <clipPath id={`capclip-${filterId}`}><polygon points={wing} /><circle cx={center} cy={center} r={bodyR} /></clipPath>
                    <g pointerEvents="none" clipPath={`url(#capclip-${filterId})`}>
                        <ellipse cx={center - bodyR * 0.3} cy={center - bodyR * 0.4} rx={bodyR * 0.55} ry={bodyR * 0.3} fill="white" opacity="0.16" filter={`url(#blur-${filterId})`} />
                        <circle cx={center + bodyR * 0.1} cy={center + bodyR * 0.15} r={bodyR * 0.85} fill="black" opacity="0.12" filter={`url(#blur-${filterId})`} />
                    </g>
                    {/* white indicator line down the centre of the wing */}
                    <line x1={lx1} y1={ly1} x2={lx2} y2={ly2} stroke="#ffffff" strokeWidth={lineW} strokeLinecap="round" />
                </g>
            </g>
        );
    }

    return (
        <g className="knob-cap-system">
            {/* 3D Body (Offset Base) */}
            <g transform={`translate(${DEPTH_OFFSET}, ${DEPTH_OFFSET})`}>
                {renderGeometry(capR, "#111", "none", 0, angle)}
            </g>

            {/* Top Cap (Offset NW) */}
            <g transform={`translate(${-DEPTH_OFFSET}, -${DEPTH_OFFSET})`} filter={`url(#sh-${filterId})`}>
                {renderGeometry(capR, `url(#grad-${filterId})`, outlineColor, outlineThickness, angle)}

                {/* Clip the 3D glint/shadow to the cap SHAPE so the reflection (and
                    its blur halo) never spills outside the cap edge — matters most
                    for gear/octagon caps where a round glint would poke past. */}
                <clipPath id={`capclip-${filterId}`}>
                    {renderGeometry(capR, "#fff", "none", 0, angle)}
                </clipPath>
                <g pointerEvents="none" clipPath={`url(#capclip-${filterId})`}>
                    <circle cx={center + capR * 0.1} cy={center + capR * 0.1} r={capR * 0.9} fill="black" opacity="0.15" filter={`url(#blur-${filterId})`} />
                    <ellipse cx={center - capR * 0.4} cy={center - capR * 0.5} rx={capR * 0.55} ry={capR * 0.28} fill="white" opacity="0.13" filter={`url(#blur-${filterId})`} />
                    <path
                        d={describeArc(center, center, capR - 3, 180, 270)}
                        fill="none" stroke="white" strokeWidth="2" strokeOpacity="0.22" filter={`url(#blur-${filterId})`}
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
    const isFender = ((cosmetics.style_overrides?.knob_style || styling.knob_style || cosmetics.visualization || c.knob_style || '').toLowerCase()) === 'fender';
    // Endless / infinite dial: drag and wheel WRAP modulo (max-min) instead of clamp.
    const isInfinity = !!(c.interaction?.infinity || c.infinity);
    const _wrapOrClamp = (v) => {
        const range = max - min;
        if (isInfinity && range > 0) return min + ((v - min) % range + range) % range;
        return Math.max(min, Math.min(max, v));
    };
    // Panner: knob outputs TWO values [leftPct, rightPct] (each 0-100). Middle
    // position = [50, 50]. Linear pan: position 0 -> [100,0], pos max -> [0,100].
    // `value` may arrive as the [L,R] array or as a single position number.
    const isPanner = ((cosmetics.style_overrides?.knob_style || styling.knob_style || cosmetics.visualization || c.knob_style || '').toLowerCase()) === 'panner';
    const _mid = (min + max) / 2;
    const _posOf = (v) => Array.isArray(v) ? Number(v[1] ?? _mid) : Number(v ?? _mid);
    const displayValue = isPanner ? _posOf(value) : value;
    const fireChange = (newPos) => {
        if (isPanner) {
            const r = (max - min) || 1;
            const norm = (newPos - min) / r;
            const left = (1 - norm) * 100, right = norm * 100;
            onChange([Math.round(left * 10) / 10, Math.round(right * 10) / 10]);
        } else onChange(newPos);
    };

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
        // Alt-click snaps the knob to its default value (no drag).
        if (e.altKey) {
            const dv = c.domain?.primary?.value_default ?? c.value?.default_value ?? c.value_default;
            const def = (dv !== undefined && dv !== null) ? Number(dv) : (isPanner ? _mid : min);
            fireChange(_wrapOrClamp(Number.isFinite(def) ? def : _mid));
            return;
        }
        setIsDragging(true);
        startYRef.current = e.clientY;
        startValRef.current = isPanner ? _posOf(value)
            : (value !== undefined && value !== null ? value : min);
        e.target.setPointerCapture(e.pointerId);
    };

    const handlePointerMove = (e) => {
        if (!isDragging) return;
        const deltaY = startYRef.current - e.clientY;
        const range = max - min;
        const deltaVal = (deltaY / 150) * range;
        const next = _wrapOrClamp(Math.round((startValRef.current + deltaVal) * 100) / 100);
        fireChange(next);
    };

    const handlePointerUp = (e) => {
        setIsDragging(false);
        e.target.releasePointerCapture(e.pointerId);
    };

    // Mouse wheel: nudge the value. One notch steps by the configured step
    // (domain.primary.step) or 2% of the range. Scroll up = increase.
    // NOTE: must be a NON-PASSIVE native listener so e.preventDefault() can stop
    // a scrollable ancestor (OcaBin overflow:auto) from eating the wheel — React's
    // onWheel is passive, so it fires but the panel scrolls away and the knob
    // looks unresponsive. The handler is stored in a ref so the once-attached
    // listener always sees the latest value/min/max/onChange.
    const svgRef = React.useRef(null);
    const wheelRef = React.useRef(null);
    wheelRef.current = (e) => {
        const range = max - min;
        if (!range) return;
        const sc = parseFloat(c.domain?.primary?.step ?? c.step);
        const step = (Number.isFinite(sc) && sc > 0) ? sc : range / 50;
        const dir = e.deltaY < 0 ? 1 : -1;
        const cur = Number(isPanner ? _posOf(value)
            : ((value !== undefined && value !== null) ? value : min));
        let next = _wrapOrClamp(cur + dir * step);
        // Snap to the step grid so a sub-0.01 step (e.g. a fine dial) isn't rounded to "no change".
        next = Math.round(next / step) * step;
        const dec = (String(step).split('.')[1] || '').length;
        fireChange(parseFloat(next.toFixed(Math.min(10, dec))));
    };
    React.useEffect(() => {
        const el = svgRef.current;
        if (!el) return;
        const onWheel = (e) => { e.preventDefault(); wheelRef.current && wheelRef.current(e); };
        el.addEventListener('wheel', onWheel, { passive: false });
        return () => el.removeEventListener('wheel', onWheel);
    }, []);

    // 3. Coordinate Sync
    const { startAngle, extent, pointerAngleDeg, norm } = getKnobAngles(c, displayValue, min, max);
    const filterId = `knob-${c.id || Math.random().toString(36).substr(2, 9)}`;

    // --- FENDER (Strat) cap: only the NUMBERS + knurl rotate with the value; the
    // 3D lighting (skirt/dome GRADIENTS and the drop SHADOW) stays STATIC (fixed
    // light source). A FIXED pointer marks the current number. The face is
    // pointer-transparent + svg userSelect:none so the knob grabs/drags cleanly. ---
    if (isFender) {
        const sweep = (cosmetics.scale?.sweep ?? c.sweep ?? 300);
        const ptrPos = (cosmetics.pointer?.position || c.pointer_position || c.fender_pointer || 'top').toLowerCase();
        const sigP = ptrPos === 'right' ? 90 : ptrPos === 'bottom' ? 180 : ptrPos === 'left' ? 270 : 0;
        const N = Math.max(2, Math.round(cosmetics.scale?.count ?? 11));
        const body = styling.fill_color || colors.primary || '#eeeeee';
        const numColor = colors.text || styling.tick_color || '#caa44a';
        const gTop = shadeHex(body, 0.24), gBot = shadeHex(body, -0.34);
        const skirtR = radius * 0.97, ringR = radius * 0.66, bodyR = radius * 0.54, rNum = radius * 0.82;
        // Number font size: configurable via cosmetics.scale.text_size (or .font_size,
        // or top-level number_size). Default is 25% smaller than the previous 2x size.
        const _numFontCfg = cosmetics.scale?.text_size ?? cosmetics.scale?.font_size ?? c.number_size ?? null;
        const numFont = (_numFontCfg != null) ? parseFloat(_numFontCfg) : Math.max(11, radius * 0.195);
        const faceRot = -norm * sweep;
        const sxp = (sig, r) => center + r * Math.sin(sig * Math.PI / 180);
        const syp = (sig, r) => center - r * Math.cos(sig * Math.PI / 180);
        // Numbers + short ticks (rotate with the knob; flat colour, no gradient).
        const marks = [];
        for (let k = 0; k < N; k++) {
            const nk = (N > 1) ? k / (N - 1) : 0;
            const vk = min + nk * (max - min), sig = sigP + nk * sweep;
            marks.push(<line key={'t' + k} x1={sxp(sig, skirtR * 0.88)} y1={syp(sig, skirtR * 0.88)} x2={sxp(sig, skirtR * 0.96)} y2={syp(sig, skirtR * 0.96)} stroke={numColor} strokeWidth={1.5} strokeLinecap="round" />);
            marks.push(<text key={'n' + k} x={sxp(sig, rNum)} y={syp(sig, rNum)} fill={numColor} fontSize={numFont} fontFamily="Arial" fontWeight="bold" textAnchor="middle" dominantBaseline="central">{Math.round(vk)}</text>);
        }
        const ribs = [], M = 48;
        for (let j = 0; j < M; j++) {
            const sig = j * 360 / M;
            ribs.push(<line key={'r' + j} x1={sxp(sig, bodyR)} y1={syp(sig, bodyR)} x2={sxp(sig, ringR)} y2={syp(sig, ringR)} stroke={shadeHex(body, -0.5)} strokeWidth={1} opacity="0.5" />);
        }
        const pr0 = skirtR + 2, pr1 = skirtR - radius * 0.16, pw = radius * 0.07, sr = sigP * Math.PI / 180;
        const ptr = `${sxp(sigP, pr1)},${syp(sigP, pr1)} `
            + `${center + pr0 * Math.sin(sr) + pw * Math.cos(sr)},${center - pr0 * Math.cos(sr) + pw * Math.sin(sr)} `
            + `${center + pr0 * Math.sin(sr) - pw * Math.cos(sr)},${center - pr0 * Math.cos(sr) - pw * Math.sin(sr)}`;
        return (
            <div ref={wrapRef} style={{ width: fluid ? '100%' : size, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <svg ref={svgRef} width={size} height={size} viewBox={`0 0 ${size} ${size}`}
                style={{ touchAction: 'none', cursor: 'ns-resize', overflow: 'visible', userSelect: 'none' }}
                onPointerDown={handlePointerDown} onPointerMove={handlePointerMove}
                onPointerUp={handlePointerUp} onPointerCancel={handlePointerUp}>
                <defs>
                    <radialGradient id={`fskirt-${filterId}`} cx="42%" cy="38%" r="72%">
                        <stop offset="0%" stopColor={shadeHex(body, 0.16)} /><stop offset="72%" stopColor={body} /><stop offset="100%" stopColor={shadeHex(body, -0.30)} />
                    </radialGradient>
                    <radialGradient id={`fbody-${filterId}`} cx="40%" cy="35%" r="75%">
                        <stop offset="0%" stopColor={gTop} /><stop offset="60%" stopColor={body} /><stop offset="100%" stopColor={gBot} />
                    </radialGradient>
                    <filter id={`sh-${filterId}`} x="-50%" y="-50%" width="200%" height="200%">
                        <feDropShadow dx="2" dy="2" stdDeviation="3" floodColor="#000" floodOpacity="0.5"/>
                    </filter>
                    <filter id={`blur-${filterId}`}><feGaussianBlur stdDeviation="2" /></filter>
                </defs>
                {/* STATIC lit skirt — gradient + drop shadow do NOT rotate */}
                <circle cx={center} cy={center} r={skirtR} fill={`url(#fskirt-${filterId})`} stroke="#222" strokeWidth="1" filter={`url(#sh-${filterId})`} pointerEvents="none" />
                {/* ROTATING printed face: knurl + ticks + numbers (flat colour) */}
                <g transform={`rotate(${faceRot} ${center} ${center})`} pointerEvents="none">
                    {ribs}
                    {marks}
                </g>
                {/* STATIC lit dome — gradient + glint do NOT rotate. Shifted slightly
                    upward to suggest height (cylinder side peeking below the dome). */}
                <ellipse cx={center} cy={center + radius * 0.02} rx={bodyR * 1.0} ry={bodyR * 0.18} fill="#000" opacity="0.35" filter={`url(#blur-${filterId})`} pointerEvents="none" />
                <g pointerEvents="none" transform={`translate(0 ${-radius * 0.07})`}>
                    <circle cx={center} cy={center} r={bodyR} fill={`url(#fbody-${filterId})`} stroke={shadeHex(body, -0.4)} strokeWidth="1" />
                    <ellipse cx={center - bodyR * 0.32} cy={center - bodyR * 0.4} rx={bodyR * 0.5} ry={bodyR * 0.26} fill="white" opacity="0.16" filter={`url(#blur-${filterId})`} />
                </g>
                {/* FIXED reference pointer (does NOT rotate) */}
                <polygon points={ptr} fill={indicatorColor} stroke="#000" strokeWidth="0.5" pointerEvents="none" />
            </svg>
            </div>
        );
    }

    return (
        <div ref={wrapRef} style={{ width: fluid ? '100%' : size, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <svg
            ref={svgRef}
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
                    {/* Softer top-to-bottom shading: gentler top highlight, base held
                        through the middle, lifted (less black) bottom. */}
                    <stop offset="0%" stopColor="#484848" />
                    <stop offset="50%" stopColor={baseColor} />
                    <stop offset="100%" stopColor="#1e1e1e" />
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
// Lighten (amt>0) or darken (amt<0) a #rgb/#rrggbb colour. Named colours pass
// through unchanged (chicken/marconi gradients then read as a flat colour).
function shadeHex(col, amt) {
    if (typeof col !== 'string') return col;
    let c = col.trim();
    if (/^#([0-9a-fA-F]{3})$/.test(c)) c = '#' + c.slice(1).split('').map(x => x + x).join('');
    const m = /^#([0-9a-fA-F]{6})$/.exec(c);
    if (!m) return col;
    const n = parseInt(m[1], 16);
    const f = (v) => Math.max(0, Math.min(255, Math.round(v + amt * 255)));
    const r = f((n >> 16) & 255), g = f((n >> 8) & 255), b = f(n & 255);
    return '#' + [r, g, b].map(v => v.toString(16).padStart(2, '0')).join('');
}

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