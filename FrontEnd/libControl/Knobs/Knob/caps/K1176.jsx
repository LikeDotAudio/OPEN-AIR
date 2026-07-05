/**
 * Header: K1176.jsx
 * Purpose: K1176 component or utility.
 * Description: Handles logic and rendering for K1176 component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// Knob/caps/K1176.jsx — UA-1176 compressor style knob cap.
// Fluted body + polished metallic top, with optional wide flange (white
// indicator line on it) and optional chicken-foot pointer tab.
// Config: cosmetics.flange.{show,color,size}, cosmetics.foot.{show,color,length},
//         cosmetics.styling.cap_color, cosmetics.styling.fill_color | colors.primary.
const KnobCap1176 = ({ center, radius, angle, config, filterId, indicatorColor }) => {
    const DEPTH_OFFSET = 1.5;
    const shadeHex = window.shadeHex;
    const c = config || {};
    const cosmetics = c.cosmetics || {};
    const styling = cosmetics.styling || {};
    const colors = cosmetics.colors || {};

    const body = styling.fill_color || colors.primary || '#1c1c1c';
    const cap = colors.cap || styling.cap_color || '#cfd2d6';
    const fl = cosmetics.flange || {}, fo = cosmetics.foot || {};
    const showFlange = fl.show !== false;
    const showFoot = !!fo.show;
    const flangeColor = fl.color || body;
    const flangeR = (fl.size != null ? parseFloat(fl.size) : 0.95) * radius;
    const footColor = fo.color || '#ffffff';
    const footLen = (fo.length != null ? parseFloat(fo.length) : 0.18) * radius;
    const bodyR = radius * 0.55, capR = radius * 0.46;
    const rad = angle * Math.PI / 180;
    return (
        <g className="knob-cap-system k1176">
            <defs>
                <radialGradient id={`fl-${filterId}`} cx="40%" cy="38%" r="78%">
                    <stop offset="0%" stopColor={shadeHex(flangeColor, 0.20)} />
                    <stop offset="65%" stopColor={flangeColor} />
                    <stop offset="100%" stopColor={shadeHex(flangeColor, -0.45)} />
                </radialGradient>
                <linearGradient id={`bd-${filterId}`} x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor={shadeHex(body, 0.15)} />
                    <stop offset="55%" stopColor={body} />
                    <stop offset="100%" stopColor={shadeHex(body, -0.45)} />
                </linearGradient>
                <radialGradient id={`cp-${filterId}`} cx="42%" cy="38%" r="78%">
                    <stop offset="0%" stopColor={shadeHex(cap, 0.20)} />
                    <stop offset="55%" stopColor={cap} />
                    <stop offset="100%" stopColor={shadeHex(cap, -0.30)} />
                </radialGradient>
            </defs>
            {showFlange && (<>
                <circle cx={center} cy={center} r={flangeR} fill={`url(#fl-${filterId})`} stroke={shadeHex(flangeColor, -0.55)} strokeWidth="1" filter={`url(#sh-${filterId})`} />
                <line x1={center + bodyR * Math.cos(rad)} y1={center - bodyR * Math.sin(rad)}
                      x2={center + flangeR * 0.96 * Math.cos(rad)} y2={center - flangeR * 0.96 * Math.sin(rad)}
                      stroke="#ffffff" strokeWidth={Math.max(2, radius * 0.04)} strokeLinecap="round" />
            </>)}
            {showFoot && (() => {
                const perp = rad + Math.PI / 2;
                const fHW = bodyR * 0.20, fOut = bodyR + footLen;
                const bx = center + (bodyR - 1) * Math.cos(rad), by = center - (bodyR - 1) * Math.sin(rad);
                const ox = center + fOut * Math.cos(rad), oy = center - fOut * Math.sin(rad);
                const pts = [
                    `${bx + fHW * Math.cos(perp)},${by - fHW * Math.sin(perp)}`,
                    `${ox + fHW * 0.55 * Math.cos(perp)},${oy - fHW * 0.55 * Math.sin(perp)}`,
                    `${ox - fHW * 0.55 * Math.cos(perp)},${oy + fHW * 0.55 * Math.sin(perp)}`,
                    `${bx - fHW * Math.cos(perp)},${by + fHW * Math.sin(perp)}`,
                ].join(' ');
                return <polygon points={pts} fill={footColor} stroke="#0a0a0a" strokeWidth="0.5" strokeLinejoin="round" />;
            })()}
            <g transform={`translate(${DEPTH_OFFSET}, ${DEPTH_OFFSET})`}>
                <circle cx={center} cy={center} r={bodyR} fill="#000" />
            </g>
            <g transform={`translate(${-DEPTH_OFFSET}, -${DEPTH_OFFSET})`} filter={`url(#sh-${filterId})`}>
                <circle cx={center} cy={center} r={bodyR} fill={`url(#bd-${filterId})`} stroke={shadeHex(body, -0.5)} strokeWidth="1" />
                <g pointerEvents="none">
                    {[...Array(44)].map((_, j) => {
                        const t = (j / 44) * 2 * Math.PI;
                        return <line key={j}
                            x1={center + (capR + 1) * Math.cos(t)} y1={center - (capR + 1) * Math.sin(t)}
                            x2={center + (bodyR - 1) * Math.cos(t)} y2={center - (bodyR - 1) * Math.sin(t)}
                            stroke={shadeHex(body, -0.55)} strokeWidth="1" opacity="0.7" />;
                    })}
                </g>
                <circle cx={center} cy={center} r={capR} fill={`url(#cp-${filterId})`} stroke={shadeHex(cap, -0.4)} strokeWidth="1" />
                <g pointerEvents="none">
                    {[...Array(48)].map((_, j) => {
                        const t = (j / 48) * 2 * Math.PI;
                        const op = 0.05 + 0.10 * (0.5 + 0.5 * Math.sin(j * 2.3));
                        return <line key={j}
                            x1={center} y1={center}
                            x2={center + capR * Math.cos(t)} y2={center - capR * Math.sin(t)}
                            stroke="#ffffff" strokeWidth="0.6" opacity={op} />;
                    })}
                </g>
                <ellipse cx={center - capR * 0.32} cy={center - capR * 0.4} rx={capR * 0.55} ry={capR * 0.28} fill="white" opacity="0.22" filter={`url(#blur-${filterId})`} />
            </g>
        </g>
    );
};
window.KnobCap1176 = KnobCap1176;
