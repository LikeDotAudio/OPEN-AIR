// Knob/caps/API.jsx — 4-lobed rounded-square shell with a bright LED-style
// centre disc (colors.primary) and a prominent corner pointer-notch that
// protrudes at the value angle. Outer shell defaults to dark; styling.fill_color
// overrides it.
const KnobCapAPI = ({ center, radius, angle, config, filterId, indicatorColor }) => {
    const DEPTH_OFFSET = 1.5;
    const shadeHex = window.shadeHex;
    const c = config || {};
    const cosmetics = c.cosmetics || {};
    const styling = cosmetics.styling || {};
    const colors = cosmetics.colors || {};

    const face = colors.primary || indicatorColor || '#33A1FD';
    const shell = styling.fill_color || '#1c1c1c';
    const shellEdge = shadeHex(shell, 0.30);
    const rad = angle * Math.PI / 180;
    const bodyR0 = radius * 0.78, lobeAmp = radius * 0.10;
    const insetR = radius * 0.50;
    const notchLen = radius * 0.20, notchHW = radius * 0.12;
    const STEPS = 72;
    const bodyPts = [];
    for (let i = 0; i < STEPS; i++) {
        const t = (i / STEPS) * 2 * Math.PI;
        const r = bodyR0 + lobeAmp * Math.cos(4 * (t - rad));
        bodyPts.push(`${center + r * Math.cos(t)},${center - r * Math.sin(t)}`);
    }
    const body = bodyPts.join(' ');
    const baseR = bodyR0 + lobeAmp;
    const tipLen = baseR + notchLen;
    const perp = rad + Math.PI / 2;
    const tipX = center + tipLen * Math.cos(rad), tipY = center - tipLen * Math.sin(rad);
    const bx = center + baseR * Math.cos(rad), by = center - baseR * Math.sin(rad);
    const b1x = bx + notchHW * Math.cos(perp), b1y = by - notchHW * Math.sin(perp);
    const b2x = bx - notchHW * Math.cos(perp), b2y = by + notchHW * Math.sin(perp);
    const notch = `${tipX},${tipY} ${b1x},${b1y} ${b2x},${b2y}`;
    return (
        <g className="knob-cap-system api">
            <defs>
                <radialGradient id={`apiface-${filterId}`} cx="45%" cy="35%" r="80%">
                    <stop offset="0%" stopColor={shadeHex(face, 0.25)} />
                    <stop offset="65%" stopColor={face} />
                    <stop offset="100%" stopColor={shadeHex(face, -0.30)} />
                </radialGradient>
            </defs>
            <g transform={`translate(${DEPTH_OFFSET}, ${DEPTH_OFFSET})`}>
                <polygon points={body} fill="#000" strokeLinejoin="round" />
                <polygon points={notch} fill="#000" strokeLinejoin="round" />
            </g>
            <g transform={`translate(${-DEPTH_OFFSET}, -${DEPTH_OFFSET})`} filter={`url(#sh-${filterId})`}>
                <polygon points={body} fill={shell} stroke={shellEdge} strokeWidth="1" strokeLinejoin="round" />
                <polygon points={notch} fill={shell} stroke={shellEdge} strokeWidth="1" strokeLinejoin="round" />
                <circle cx={center} cy={center} r={insetR} fill={`url(#apiface-${filterId})`} stroke={shadeHex(face, -0.4)} strokeWidth="1" />
                <ellipse cx={center - insetR * 0.32} cy={center - insetR * 0.4} rx={insetR * 0.55} ry={insetR * 0.28} fill="white" opacity="0.20" filter={`url(#blur-${filterId})`} />
            </g>
        </g>
    );
};
window.KnobCapAPI = KnobCapAPI;
