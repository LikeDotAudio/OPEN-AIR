/**
 * Header: Marconi.jsx
 * Purpose: Marconi component or utility.
 * Description: Handles logic and rendering for Marconi component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// Knob/caps/Marconi.jsx — "Elma" British wing knob cap.
// ONE solid rectangular wing that passes THROUGH the body and protrudes the
// same distance on BOTH sides; the white indicator line is drawn only on the
// pointer side. Body sits on a metallic skirt.
const KnobCapMarconi = ({ center, radius, angle, config, filterId, indicatorColor }) => {
    const DEPTH_OFFSET = 1.5;
    const shadeHex = window.shadeHex;
    const c = config || {};
    const cosmetics = c.cosmetics || {};
    const styling = cosmetics.styling || {};
    const colors = cosmetics.colors || {};
    const outlineColor = styling.outline_color || c.knob_outline_color || '#444';
    const outlineThickness = styling.outline_thickness !== undefined ? styling.outline_thickness : (c.knob_outline_thickness || 0);

    const body = styling.fill_color || colors.primary || indicatorColor || '#9aa3ad';
    const gTop = shadeHex(body, 0.30), gBot = shadeHex(body, -0.42);
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
                <line x1={lx1} y1={ly1} x2={lx2} y2={ly2} stroke="#ffffff" strokeWidth={lineW} strokeLinecap="round" />
            </g>
        </g>
    );
};
window.KnobCapMarconi = KnobCapMarconi;
