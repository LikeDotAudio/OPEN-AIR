/**
 * Header: Standard.jsx
 * Purpose: Standard component or utility.
 * Description: Handles logic and rendering for Standard component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// Knob/caps/Standard.jsx — the DEFAULT knob cap (circle / octagon / gear cap
// shapes with the standard separate pointer). Used when no specialized
// visualization is set. The shape comes from style_overrides.shape OR is
// inferred from the visualization style ('gear'/'octagon'/'circle').
const KnobCapStandard = ({ center, radius, angle, config, filterId, indicatorColor }) => {
    const DEPTH_OFFSET = 1.5;
    const shadeHex = window.shadeHex;
    const describeArc = window.describeArc;
    const c = config || {};
    const cosmetics = c.cosmetics || {};
    const styling = cosmetics.styling || {};
    const overrides = cosmetics.style_overrides || {};
    const pointer = cosmetics.pointer || {};

    const knobStyle = (overrides.knob_style || styling.knob_style || cosmetics.visualization || c.knob_style || 'standard').toLowerCase();
    const defaultShape = (knobStyle === 'gear' || knobStyle === 'octagon' || knobStyle === 'circle') ? knobStyle : 'circle';
    const knobShape = (overrides.shape || styling.shape || c.shape || defaultShape).toLowerCase();

    const gearTeeth = styling.teeth || c.knob_teeth || 8;
    const outlineColor = styling.outline_color || c.knob_outline_color || '#444';
    const outlineThickness = styling.outline_thickness !== undefined ? styling.outline_thickness : (c.knob_outline_thickness || 0);
    const noCenter = styling.no_center || c.no_center || false;
    const capScale = styling.cap_scale !== undefined ? styling.cap_scale : 0.7;
    const capR = radius * capScale;

    const pointerStyle = (pointer.style || c.pointer_style || 'line').toLowerCase();
    const pointerLength = (pointer.length != null) ? pointer.length
        : ((c?.pointer_length != null) ? c.pointer_length : (radius - 2));
    const pointerOffset = (pointer.offset != null) ? pointer.offset
        : ((c?.pointer_offset != null) ? c.pointer_offset : 0);

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
            const nLen = 6;
            const nx1 = center + (pointerOffset + pointerLength - nLen) * Math.cos(rad);
            const ny1 = center - (pointerOffset + pointerLength - nLen) * Math.sin(rad);
            return <line x1={nx1} y1={ny1} x2={x2} y2={y2} stroke={indicatorColor} strokeWidth="4" strokeLinecap="butt" />;
        } else if (pointerStyle === 'thin') {
            return <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={indicatorColor} strokeWidth="1" strokeLinecap="round" />;
        } else if (pointerStyle === 'block') {
            return <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={indicatorColor} strokeWidth="6" strokeLinecap="butt" />;
        } else if (pointerStyle === 'tapered') {
            const perp = rad + Math.PI / 2;
            const bh = 4;
            const bx1 = x1 + bh * Math.cos(perp), by1 = y1 - bh * Math.sin(perp);
            const bx2 = x1 - bh * Math.cos(perp), by2 = y1 + bh * Math.sin(perp);
            return <polygon points={`${x2},${y2} ${bx1},${by1} ${bx2},${by2}`} fill={indicatorColor} />;
        } else if (pointerStyle === 'vintage') {
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
            <g transform={`translate(${DEPTH_OFFSET}, ${DEPTH_OFFSET})`}>
                {renderGeometry(capR, "#111", "none", 0, angle)}
            </g>
            <g transform={`translate(${-DEPTH_OFFSET}, -${DEPTH_OFFSET})`} filter={`url(#sh-${filterId})`}>
                {renderGeometry(capR, `url(#grad-${filterId})`, outlineColor, outlineThickness, angle)}
                <clipPath id={`capclip-${filterId}`}>
                    {renderGeometry(capR, "#fff", "none", 0, angle)}
                </clipPath>
                <g pointerEvents="none" clipPath={`url(#capclip-${filterId})`}>
                    <circle cx={center + capR * 0.1} cy={center + capR * 0.1} r={capR * 0.9} fill="black" opacity="0.15" filter={`url(#blur-${filterId})`} />
                    <ellipse cx={center - capR * 0.4} cy={center - capR * 0.5} rx={capR * 0.55} ry={capR * 0.28} fill="white" opacity="0.13" filter={`url(#blur-${filterId})`} />
                    <path d={describeArc(center, center, capR - 3, 180, 270)}
                        fill="none" stroke="white" strokeWidth="2" strokeOpacity="0.22" filter={`url(#blur-${filterId})`} />
                </g>
                {!noCenter && <circle cx={center} cy={center} r={3} fill={indicatorColor} />}
                {renderPointer(capR, angle)}
            </g>
        </g>
    );
};
window.KnobCapStandard = KnobCapStandard;
