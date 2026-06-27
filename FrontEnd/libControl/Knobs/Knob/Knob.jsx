/**
 * Knob Orchestrator (slim — cap renderers live in caps/*.jsx)
 *
 * Architecture
 *   - getKnobAngles + KnobTicks      : motion logic + scale ring.
 *   - shadeHex / describeArc / polarToCartesian : shared helpers (exposed on window).
 *   - Knob (orchestrator)            : interaction state (drag/wheel/alt/infinity/panner),
 *                                       fluid measure, default-snap, and DISPATCH to a
 *                                       cap renderer module (window.KnobCap<Name>).
 *
 * Cap renderers — ONE FILE PER KNOB TYPE under `caps/`:
 *   caps/Standard.jsx  → window.KnobCapStandard  (circle / octagon / gear default)
 *   caps/Chicken.jsx   → window.KnobCapChicken   (beak + bum tail)
 *   caps/Marconi.jsx   → window.KnobCapMarconi   (rectangular wing on a metal skirt)
 *   caps/British.jsx   → window.KnobCapBritish   (fluted + optional cap/ring/window)
 *   caps/Pedal.jsx     → window.KnobCapPedal     (round body + ears + white line)
 *   caps/K1176.jsx     → window.KnobCap1176      (UA-1176 fluted + cap + flange + foot)
 *   caps/API.jsx       → window.KnobCapAPI       (4-lobed shell + LED disc + notch)
 *   caps/Fender.jsx    → window.KnobCapFender    (orchestrator-level — face rotates,
 *                                                  pointer fixed; receives handlers)
 *
 * Add a new style by dropping another `caps/<Name>.jsx`, registering on
 * window, listing in index.html, and adding one line to CAP_DISPATCH below.
 */

// --- HELPERS (exposed on window so cap modules can reuse them) ------------------
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
function polarToCartesian(centerX, centerY, radius, angleInDegrees) {
    const rad = angleInDegrees * Math.PI / 180.0;
    return { x: centerX + (radius * Math.cos(rad)), y: centerY - (radius * Math.sin(rad)) };
}
function describeArc(x, y, radius, startAngle, endAngle) {
    const start = polarToCartesian(x, y, radius, endAngle);
    const end = polarToCartesian(x, y, radius, startAngle);
    const largeArcFlag = Math.abs(endAngle - startAngle) <= 180 ? "0" : "1";
    return ["M", start.x, start.y, "A", radius, radius, 0, largeArcFlag, 0, end.x, end.y].join(" ");
}
window.shadeHex = shadeHex;
window.describeArc = describeArc;
window.polarToCartesian = polarToCartesian;

// --- MOTION & ANGLES ------------------------------------------------------------
const getKnobAngles = (config, value, min, max) => {
    const knobStyle = (config?.cosmetics?.style_overrides?.knob_style ||
                      config?.cosmetics?.styling?.knob_style ||
                      config?.cosmetics?.visualization || 'standard').toLowerCase();
    const clamp = (val, min, max) => Math.max(min, Math.min(max, val));
    const boundedValue = clamp(value !== undefined && value !== null ? value : min, min, max);
    const norm = (boundedValue - min) / ((max - min) || 1);
    let startAngle = 240, extent = -300, pointerAngleDeg;
    if (knobStyle === 'panner') {
        startAngle = 90; extent = 135;
        const mid = (min + max) / 2;
        const normFromCenter = (boundedValue - mid) / ((max - min) / 2 || 1);
        pointerAngleDeg = startAngle + (-normFromCenter * extent);
    } else if (knobStyle === 'dial') {
        startAngle = 90; extent = -360;
        pointerAngleDeg = startAngle + (norm * extent);
    } else {
        pointerAngleDeg = startAngle + (norm * extent);
    }
    return { startAngle, extent, pointerAngleDeg, norm };
};

// --- TICK SCALE (around the knob track) -----------------------------------------
const KnobTicks = ({ center, radius, arcWidth, config, filterId, min = 0, max = 100 }) => {
    const scale = config?.cosmetics?.scale || config?.scale || {};
    const colors = config?.cosmetics?.colors || {};
    const showTicks = scale.show !== undefined ? scale.show : (config?.show_ticks || false);
    if (!showTicks) return null;
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
                    fill={tickColor} fontSize="7" fontFamily="Arial" textAnchor="middle" alignmentBaseline="middle">{label}</text>
            );
        } else {
            items.push(<line key={i} x1={ox} y1={oy} x2={ex} y2={ey} stroke={tickColor} strokeWidth={tickThickness} />);
        }
    }
    return <g className="knob-ticks">{items}</g>;
};

// --- CAP DISPATCH ---------------------------------------------------------------
// Resolve a window.KnobCap<Name> renderer by style/shape. The lookup is lazy so
// the cap modules can load in any order (they all share the same load tick).
function resolveCap(knobStyle, knobShape) {
    const k = (knobStyle || '').toLowerCase();
    const s = (knobShape || '').toLowerCase();
    const M = (key) => ({
        chicken: window.KnobCapChicken,
        marconi: window.KnobCapMarconi,
        api: window.KnobCapAPI,
        '1176': window.KnobCap1176,
        pedal: window.KnobCapPedal,
        british: window.KnobCapBritish,
        moog: window.KnobCapMoog,
        'wbs-elma': window.KnobCapWBSElma,
        wbselma: window.KnobCapWBSElma,
    })[key];
    return M(k) || M(s) || window.KnobCapStandard;
}

// --- MAIN ORCHESTRATOR ----------------------------------------------------------
const Knob = ({ value, onChange, config, size: defaultSize = 80 }) => {
    const c = config || {};
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

    // Resolve which "kind" of knob this is.
    const _styleStr = (cosmetics.style_overrides?.knob_style || styling.knob_style || cosmetics.visualization || c.knob_style || '').toLowerCase();
    const _shapeStr = (cosmetics.style_overrides?.shape || styling.shape || c.shape || '').toLowerCase();
    const isFender = _styleStr === 'fender';
    const isInfinity = !!(c.interaction?.infinity || c.infinity);
    const isPanner = _styleStr === 'panner';

    // Wrap (infinity) vs clamp helper.
    const _wrapOrClamp = (v) => {
        const range = max - min;
        if (isInfinity && range > 0) return min + ((v - min) % range + range) % range;
        return Math.max(min, Math.min(max, v));
    };
    // Panner: knob outputs TWO values [leftPct, rightPct] (each 0-100).
    const _mid = (min + max) / 2;
    const _posOf = (v) => Array.isArray(v) ? Number(v[1] ?? _mid) : Number(v ?? _mid);

    const [localVal, setLocalVal] = React.useState(null);
    const dwellTimerRef = React.useRef(null);

    const displayValue = localVal !== null ? localVal : (isPanner ? _posOf(value) : value);
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

    // Interaction (drag).
    const [isDragging, setIsDragging] = React.useState(false);
    const startYRef = React.useRef(0);
    const startValRef = React.useRef(0);

    const handlePointerDown = (e) => {
        if (e.altKey) {
            const dv = c.domain?.primary?.value_default ?? c.value?.default_value ?? c.value_default;
            const def = (dv !== undefined && dv !== null) ? Number(dv) : (isPanner ? _mid : min);
            const nv = _wrapOrClamp(Number.isFinite(def) ? def : _mid);
            fireChange(nv);
            setLocalVal(nv);
            clearTimeout(dwellTimerRef.current);
            dwellTimerRef.current = setTimeout(() => setLocalVal(null), 500);
            return;
        }
        setIsDragging(true);
        startYRef.current = e.clientY;
        const cv = isPanner ? _posOf(value) : (value !== undefined && value !== null ? value : min);
        startValRef.current = cv;
        setLocalVal(cv);
        clearTimeout(dwellTimerRef.current);
        e.target.setPointerCapture(e.pointerId);
    };
    const handlePointerMove = (e) => {
        if (!isDragging) return;
        const deltaY = startYRef.current - e.clientY;
        const range = max - min;
        const deltaVal = (deltaY / 150) * range;
        const nv = _wrapOrClamp(Math.round((startValRef.current + deltaVal) * 100) / 100);
        setLocalVal(nv);
        fireChange(nv);
    };
    const handlePointerUp = (e) => {
        setIsDragging(false);
        e.target.releasePointerCapture(e.pointerId);
        clearTimeout(dwellTimerRef.current);
        dwellTimerRef.current = setTimeout(() => setLocalVal(null), 500);
    };

    // Wheel — non-passive native listener
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
        next = Math.round(next / step) * step;
        const dec = (String(step).split('.')[1] || '').length;
        const nv = parseFloat(next.toFixed(Math.min(10, dec)));
        setLocalVal(nv);
        fireChange(nv);
        clearTimeout(dwellTimerRef.current);
        dwellTimerRef.current = setTimeout(() => setLocalVal(null), 500);
    };
    React.useEffect(() => {
        const el = svgRef.current;
        if (!el) return;
        const onWheel = (e) => { e.preventDefault(); wheelRef.current && wheelRef.current(e); };
        el.addEventListener('wheel', onWheel, { passive: false });
        return () => el.removeEventListener('wheel', onWheel);
    }, []);

    // Angles & filter id.
    const { startAngle, extent, pointerAngleDeg, norm } = getKnobAngles(c, displayValue, min, max);
    const filterId = `knob-${c.id || Math.random().toString(36).substr(2, 9)}`;

    // FENDER takes over the whole svg (face rotates, fixed pointer); it receives
    // the orchestrator state as props (handlers, refs, sizing).
    if (isFender && window.KnobCapFender) {
        return <window.KnobCapFender
            center={center} radius={radius} norm={norm} min={min} max={max}
            config={c} filterId={filterId} indicatorColor={indicatorColor}
            size={size} fluid={fluid} wrapRef={wrapRef} svgRef={svgRef}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp} />;
    }

    // Pick the cap renderer (Standard, Chicken, Marconi, …).
    const CapComp = resolveCap(_styleStr, _shapeStr);

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

            {/* Ticks */}
            <KnobTicks center={center} radius={radius} arcWidth={arcWidth} config={c} filterId={filterId} min={min} max={max} />

            {/* Outer Bezel */}
            <circle cx={center} cy={center} r={radius + arcWidth/2 + 2} fill="none" stroke="#111" strokeWidth="1" />

            {/* Visual Cap — dispatched to caps/*.jsx */}
            {CapComp
                ? <CapComp center={center} radius={radius} angle={pointerAngleDeg}
                           config={c} filterId={filterId} indicatorColor={indicatorColor} />
                : null}
        </svg>
        </div>
    );
};

window.Knob = Knob;
