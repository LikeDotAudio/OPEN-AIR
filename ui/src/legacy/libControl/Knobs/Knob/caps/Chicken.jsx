/**
 * Header: Chicken.jsx
 * Purpose: Chicken component or utility.
 * Description: Handles logic and rendering for Chicken component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// Knob/caps/Chicken.jsx — chicken-head knob cap renderer.
// Long tapered BEAK forward + short blunt "bum" tail back, widest at the centre
// hub (per the Q-parts top view). The beak IS the indicator (no separate
// pointer). Body colour drives a glossy gradient via window.shadeHex.
const KnobCapChicken = ({ center, radius, angle, config, filterId, indicatorColor }) => {
    const DEPTH_OFFSET = 1.5;
    const shadeHex = window.shadeHex;
    const c = config || {};
    const cosmetics = c.cosmetics || {};
    const styling = cosmetics.styling || {};
    const colors = cosmetics.colors || {};
    const outlineColor = styling.outline_color || c.knob_outline_color || '#444';
    const outlineThickness = styling.outline_thickness !== undefined ? styling.outline_thickness : (c.knob_outline_thickness || 0);

    const body = styling.fill_color || colors.primary || indicatorColor || '#cccccc';
    const gTop = shadeHex(body, 0.32), gBot = shadeHex(body, -0.45), ridge = shadeHex(body, -0.5);
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
};
window.KnobCapChicken = KnobCapChicken;
