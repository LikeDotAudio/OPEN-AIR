// Knob/caps/WBSElma.jsx — WBS-ELMA (Swiss instrumentation) knob cap.
// Fluted cylindrical body with three variants driven by cosmetics:
//   • REGULAR — colored cap inset on top + white indicator line (default).
//   • WING    — small rectangular tab(s) protruding from the body edge
//               (`cosmetics.wing.show` + optional `wing.both` for two-sided).
//   • POINTER — small triangular pointer tip at the body edge
//               (`cosmetics.pointer_tip.show`).
//
// Config keys:
//   cosmetics.cap.{show,color}             colored cap inset (default show=true)
//   cosmetics.line.{color,width}           indicator line (default white)
//   cosmetics.wing.{show,color,length,both,angle}
//                                          'angle' = 'pointer'|'perpendicular' (default 'pointer')
//   cosmetics.pointer_tip.{show,color,length}
//   cosmetics.flutes                       number of body flutes (default 18)
//   cosmetics.styling.fill_color | colors.primary  body colour
//   cosmetics.colors.cap | styling.cap_color       cap-inset colour
const KnobCapWBSElma = ({ center, radius, angle, config, filterId, indicatorColor }) => {
    const DEPTH_OFFSET = 1.5;
    const shadeHex = window.shadeHex;
    const c = config || {};
    const cosmetics = c.cosmetics || {};
    const styling = cosmetics.styling || {};
    const colors = cosmetics.colors || {};

    const body = styling.fill_color || colors.primary || '#1c1c1c';
    const capCfg = cosmetics.cap || {};
    const showCap = capCfg.show !== false;
    const capColor = capCfg.color || colors.cap || styling.cap_color || '#2A52E0';
    const lineColor = (cosmetics.line && cosmetics.line.color) || '#ffffff';
    const lineW = (cosmetics.line && cosmetics.line.width != null)
        ? parseFloat(cosmetics.line.width) : Math.max(1.6, radius * 0.04);

    const wingCfg = cosmetics.wing || {};
    const showWing = !!wingCfg.show;
    const wingBoth = !!wingCfg.both;
    const wingColor = wingCfg.color || body;
    const wingLen = (wingCfg.length != null ? parseFloat(wingCfg.length) : 0.18) * radius;
    const wingPerp = wingCfg.angle === 'perpendicular';

    const tipCfg = cosmetics.pointer_tip || {};
    const showTip = !!tipCfg.show;
    const tipColor = tipCfg.color || body;
    const tipLen = (tipCfg.length != null ? parseFloat(tipCfg.length) : 0.16) * radius;

    const flutes = parseInt(cosmetics.flutes != null ? cosmetics.flutes : 18, 10);
    const bodyR = radius * 0.85;
    const lobeAmp = bodyR * 0.045;
    const capR = bodyR * 0.74;
    const rad = angle * Math.PI / 180;

    // Subtle fluted body silhouette (flutes rotate with value)
    const STEPS = flutes * 8;
    const bodyPts = [];
    for (let i = 0; i < STEPS; i++) {
        const t = (i / STEPS) * 2 * Math.PI;
        const r = bodyR + lobeAmp * Math.cos(flutes * (t - rad));
        bodyPts.push(`${center + r * Math.cos(t)},${center - r * Math.sin(t)}`);
    }
    const bodyPoly = bodyPts.join(' ');

    // Wing tab geometry. dir = +1 (pointer side) or -1 (opposite side).
    const wing = (dir) => {
        const ang = wingPerp ? (rad + Math.PI / 2) : rad;
        const perp = ang + Math.PI / 2;
        const hw = bodyR * 0.15;
        const baseR = bodyR + lobeAmp - 1;
        const outR = baseR + wingLen;
        const bx = center + dir * baseR * Math.cos(ang), by = center - dir * baseR * Math.sin(ang);
        const ox = center + dir * outR * Math.cos(ang), oy = center - dir * outR * Math.sin(ang);
        return [
            `${bx + hw * Math.cos(perp)},${by - hw * Math.sin(perp)}`,
            `${ox + hw * 0.8 * Math.cos(perp)},${oy - hw * 0.8 * Math.sin(perp)}`,
            `${ox - hw * 0.8 * Math.cos(perp)},${oy + hw * 0.8 * Math.sin(perp)}`,
            `${bx - hw * Math.cos(perp)},${by + hw * Math.sin(perp)}`,
        ].join(' ');
    };

    // Pointer-tip triangle (per image 67).
    const tipPoly = (() => {
        const perp = rad + Math.PI / 2;
        const baseR = bodyR + lobeAmp - 1;
        const outR = baseR + tipLen;
        const hwBase = bodyR * 0.10;
        const ox = center + outR * Math.cos(rad), oy = center - outR * Math.sin(rad);
        const b1x = center + baseR * Math.cos(rad) + hwBase * Math.cos(perp);
        const b1y = center - baseR * Math.sin(rad) - hwBase * Math.sin(perp);
        const b2x = center + baseR * Math.cos(rad) - hwBase * Math.cos(perp);
        const b2y = center - baseR * Math.sin(rad) + hwBase * Math.sin(perp);
        return `${ox},${oy} ${b1x},${b1y} ${b2x},${b2y}`;
    })();

    return (
        <g className="knob-cap-system wbselma">
            <defs>
                <radialGradient id={`we-${filterId}`} cx="40%" cy="35%" r="78%">
                    <stop offset="0%" stopColor={shadeHex(body, 0.20)} />
                    <stop offset="55%" stopColor={body} />
                    <stop offset="100%" stopColor={shadeHex(body, -0.42)} />
                </radialGradient>
                <radialGradient id={`wecap-${filterId}`} cx="38%" cy="32%" r="80%">
                    <stop offset="0%" stopColor={shadeHex(capColor, 0.22)} />
                    <stop offset="55%" stopColor={capColor} />
                    <stop offset="100%" stopColor={shadeHex(capColor, -0.30)} />
                </radialGradient>
            </defs>

            {/* Wing tab(s) — variant: WING */}
            {showWing && (<>
                <polygon points={wing(1)} fill="#0a0a0a" transform={`translate(${DEPTH_OFFSET}, ${DEPTH_OFFSET})`} />
                <polygon points={wing(1)} fill={wingColor} stroke={shadeHex(wingColor, -0.5)} strokeWidth="0.7" strokeLinejoin="round" filter={`url(#sh-${filterId})`} />
                {wingBoth && (<>
                    <polygon points={wing(-1)} fill="#0a0a0a" transform={`translate(${DEPTH_OFFSET}, ${DEPTH_OFFSET})`} />
                    <polygon points={wing(-1)} fill={wingColor} stroke={shadeHex(wingColor, -0.5)} strokeWidth="0.7" strokeLinejoin="round" filter={`url(#sh-${filterId})`} />
                </>)}
            </>)}

            {/* Pointer-tip triangle — variant: POINTER */}
            {showTip && (<>
                <polygon points={tipPoly} fill="#0a0a0a" transform={`translate(${DEPTH_OFFSET}, ${DEPTH_OFFSET})`} />
                <polygon points={tipPoly} fill={tipColor} stroke={shadeHex(tipColor, -0.5)} strokeWidth="0.7" strokeLinejoin="round" filter={`url(#sh-${filterId})`} />
            </>)}

            {/* Body (depth + top) */}
            <g transform={`translate(${DEPTH_OFFSET}, ${DEPTH_OFFSET})`}>
                <polygon points={bodyPoly} fill="#000" strokeLinejoin="round" />
            </g>
            <g transform={`translate(${-DEPTH_OFFSET}, -${DEPTH_OFFSET})`} filter={`url(#sh-${filterId})`}>
                <polygon points={bodyPoly} fill={`url(#we-${filterId})`} stroke={shadeHex(body, -0.5)} strokeWidth="1" strokeLinejoin="round" />

                {/* Colored cap inset (REGULAR variant — default ON) */}
                {showCap && (<>
                    <circle cx={center} cy={center} r={capR} fill={`url(#wecap-${filterId})`} stroke={shadeHex(capColor, -0.4)} strokeWidth="1" />
                    <clipPath id={`wecapclip-${filterId}`}>
                        <circle cx={center} cy={center} r={capR} />
                    </clipPath>
                    <g pointerEvents="none" clipPath={`url(#wecapclip-${filterId})`}>
                        <ellipse cx={center - capR * 0.30} cy={center - capR * 0.40} rx={capR * 0.55} ry={capR * 0.28} fill="white" opacity="0.20" filter={`url(#blur-${filterId})`} />
                    </g>
                    {/* White indicator line on the cap (from centre toward pointer edge) */}
                    <line x1={center} y1={center}
                          x2={center + capR * 0.92 * Math.cos(rad)} y2={center - capR * 0.92 * Math.sin(rad)}
                          stroke={lineColor} strokeWidth={lineW} strokeLinecap="round" />
                </>)}

                {/* No-cap variant: line goes from centre to body edge along the pointer flute */}
                {!showCap && (
                    <line x1={center} y1={center}
                          x2={center + (bodyR - 2) * Math.cos(rad)} y2={center - (bodyR - 2) * Math.sin(rad)}
                          stroke={lineColor} strokeWidth={Math.max(2, radius * 0.05)} strokeLinecap="round" />
                )}
            </g>
        </g>
    );
};
window.KnobCapWBSElma = KnobCapWBSElma;
