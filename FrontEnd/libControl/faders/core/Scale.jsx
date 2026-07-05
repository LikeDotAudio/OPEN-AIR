/**
 * Header: Scale.jsx
 * Purpose: Scale component or utility.
 * Description: Handles logic and rendering for Scale component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// Scale Component (Ticks and Labels)
// Author: Gemini (Collaborator)
// Version: 20260524.0200.0
//
// Description: Renders the fader scale. Honors:
//   style : 'simple' (tick lines) | 'dots' (markers) | 'numeric' (number labels)
//   sides : which sides carry a scale — vertical: left/right, horizontal: top/bottom
//           (string 'both'|'left'|'right'|'top'|'bottom' or an array). Default both.
// Generates MAJOR ticks at the (smart or configured) interval + SUB ticks between.

const Scale = ({
    min, max, logExponent, width, height,
    availableLength, paddingStart,
    tickSize, slotSize, capWidth,
    tickColor = 'lightgrey',
    subTickColor,
    tickTextColor,
    subTickTextColor,
    tickThickness = 1,
    customTicks = null,
    interval = null,      // explicit MAJOR interval (cosmetics.scale.interval)
    subTicks = 4,         // minor divisions BETWEEN majors (cosmetics.scale.sub_ticks)
    style = 'simple',     // simple | dots | numeric (cosmetics.scale.style)
    sides = null,         // which sides carry the scale (default: both)
    orientation = 'vertical'
}) => {

    const effSubTickColor = subTickColor || tickColor;
    const effTickTextColor = tickTextColor || tickColor;
    const effSubTickTextColor = subTickTextColor || effSubTickColor;
    const scaleStyle = String(style || 'simple').toLowerCase();
    const showNumbers = scaleStyle === 'numeric';

    // Resolve which two sides render. Vertical => left/right; horizontal => top/bottom.
    const isVert = orientation === 'vertical';
    const sideList = Array.isArray(sides)
        ? sides.map((s) => String(s).toLowerCase())
        : (sides ? [String(sides).toLowerCase()] : []);
    const wantBoth = sideList.length === 0 || sideList.includes('both');
    const sideA = isVert ? 'left' : 'top';     // "near" side
    const sideB = isVert ? 'right' : 'bottom'; // "far" side
    const showA = wantBoth || sideList.includes(sideA);
    const showB = wantBoth || sideList.includes(sideB);

    const calculateSmartInterval = (valRange) => {
        if (valRange <= 0) return 10.0;
        const rawInterval = valRange / 10.0;
        const exponent = Math.floor(Math.log10(rawInterval));
        const fractionalPart = rawInterval / Math.pow(10, exponent);
        let snapValue = 10;
        if (fractionalPart < 1.5) snapValue = 1;
        else if (fractionalPart < 3.5) snapValue = 2;
        else if (fractionalPart < 7.5) snapValue = 5;
        return snapValue * Math.pow(10, exponent);
    };

    const getTicks = () => {
        if (customTicks && Array.isArray(customTicks)) {
            return customTicks.map((v) => ({ value: v, main: true }));
        }
        const valRange = max - min;
        const major = (interval && interval > 0) ? interval : calculateSmartInterval(valRange);
        if (!(major > 0)) return [];
        const subs = Math.max(0, Math.floor(subTicks) || 0);
        const step = subs > 0 ? major / (subs + 1) : major;
        const ticks = [];
        const EPS = step * 1e-6;
        let current = Math.ceil(min / step) * step;
        let guard = 0;
        while (current <= max + EPS && guard < 100000) {
            const ratio = current / major;
            const isMain = Math.abs(ratio - Math.round(ratio)) < 1e-6;
            ticks.push({ value: current, main: isMain });
            current += step;
            guard++;
        }
        return ticks;
    };

    const calculateTickPosition = (value) => {
        const range = max - min;
        const norm = (value - min) / range;
        const displayNorm = logExponent === 1.0 ? norm : Math.pow(Math.max(1e-7, norm), 1.0 / logExponent);
        return isVert
            ? availableLength * (1 - displayNorm) + paddingStart
            : availableLength * displayNorm + paddingStart;
    };

    const ticks = getTicks();
    const containerDim = isVert ? width : height;
    // Clamp tick length so a large `size` (e.g. 1.0) can't overrun the box edge.
    const _maxTickLen = Math.max(2, containerDim / 2 - (slotSize / 2 + 2) - 2);
    const tickLengthHalf = Math.min(containerDim * tickSize, _maxTickLen);
    const subTickLengthHalf = tickLengthHalf * 0.55;
    const center = containerDim / 2;
    const TICK_LINE_GAP = 2;
    const innerGap = slotSize / 2 + TICK_LINE_GAP;
    let margin = 5;
    if (containerDim < 80) margin = 0; else if (containerDim < 100) margin = 2;
    const labelOffset = Math.max(tickLengthHalf, capWidth / 2) + margin;

    // One mark (line/dot/short-tick) on a given side for one tick.
    const renderMark = (side, pos, isMain, color, key) => {
        const len = isMain ? tickLengthHalf : subTickLengthHalf;
        const dir = (side === 'left' || side === 'top') ? -1 : 1; // outward direction
        const inner = center + dir * innerGap;
        const outer = inner + dir * len;
        if (scaleStyle === 'dots') {
            const r = isMain ? (tickThickness + 1.5) : (tickThickness + 0.5);
            return isVert
                ? <circle key={key} cx={outer} cy={pos} r={r} fill={color} />
                : <circle key={key} cx={pos} cy={outer} r={r} fill={color} />;
        }
        // simple -> full line; numeric -> short reference tick
        const end = (scaleStyle === 'numeric') ? inner + dir * Math.min(len, 4) : outer;
        return isVert
            ? <line key={key} x1={inner} y1={pos} x2={end} y2={pos} stroke={color} strokeWidth={tickThickness} />
            : <line key={key} x1={pos} y1={inner} x2={pos} y2={end} stroke={color} strokeWidth={tickThickness} />;
    };

    // A number label on a given side (majors only).
    const renderLabel = (side, pos, textColor, labelText, key) => {
        if (isVert) {
            const x = side === 'left' ? center - labelOffset : center + labelOffset;
            const anchor = side === 'left' ? 'end' : 'start';
            return <text key={key} x={x} y={pos} fill={textColor} fontSize="7" fontFamily="Arial" alignmentBaseline="middle" textAnchor={anchor}>{labelText}</text>;
        }
        const y = side === 'top' ? center - labelOffset - slotSize / 2 + 5 : center + labelOffset + slotSize / 2;
        const baseline = side === 'top' ? 'baseline' : 'hanging';
        return <text key={key} x={pos} y={y} fill={textColor} fontSize="7" fontFamily="Arial" alignmentBaseline={baseline} textAnchor="middle">{labelText}</text>;
    };

    return (
        <svg style={{ position: 'absolute', top: 0, left: 0, width, height, pointerEvents: 'none' }}>
            {ticks.map((tick, index) => {
                const pos = calculateTickPosition(tick.value);
                const isMain = tick.main;
                const color = isMain ? tickColor : effSubTickColor;
                const textColor = isMain ? effTickTextColor : effSubTickTextColor;
                const val = tick.value;
                const labelText = val === Math.floor(val) ? val.toString() : val.toFixed(1);
                const els = [];
                if (showA) els.push(renderMark(sideA, pos, isMain, color, `${index}-a`));
                if (showB) els.push(renderMark(sideB, pos, isMain, color, `${index}-b`));
                if (showNumbers && isMain) {
                    if (showA) els.push(renderLabel(sideA, pos, textColor, labelText, `${index}-la`));
                    if (showB) els.push(renderLabel(sideB, pos, textColor, labelText, `${index}-lb`));
                }
                return <g key={index}>{els}</g>;
            })}
        </svg>
    );
};

window.FaderScale = Scale;
