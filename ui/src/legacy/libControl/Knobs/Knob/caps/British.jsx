/**
 * Header: British.jsx
 * Purpose: British component or utility.
 * Description: Handles logic and rendering for British component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// Knob/caps/British.jsx — OmterElec / classic UK fluted knob cap.
// Four optional variants driven by cosmetics: knob-with-cap (polished metal
// disc on top), knob-with-ring (knurled chrome base ring), knob-with-window
// (small fixed tick marker on the ring), and knob-with-foot ("British chicken"
// — V-shaped pointer tab protruding from the body edge at the value angle).
const KnobCapBritish = ({ center, radius, angle, config, filterId, indicatorColor }) => {
    const DEPTH_OFFSET = 1.5;
    const shadeHex = window.shadeHex;
    const c = config || {};
    const cosmetics = c.cosmetics || {};
    const styling = cosmetics.styling || {};
    const colors = cosmetics.colors || {};

    const body = styling.fill_color || colors.primary || '#1c1c1c';
    const capCfg = cosmetics.cap || {}, ringCfg = cosmetics.ring || {}, winCfg = cosmetics.window || {};
    const footCfg = cosmetics.foot || {};
    const showCap = !!capCfg.show;
    const showRing = !!ringCfg.show;
    const showWindow = !!winCfg.show;
    const showFoot = !!footCfg.show;
    const capColor = capCfg.color || colors.cap || styling.cap_color || '#cfd2d6';
    const ringColor = ringCfg.color || '#cfd2d6';
    const winColor = winCfg.color || '#1c1c1c';
    const winPos = (winCfg.pos != null) ? parseFloat(winCfg.pos) : 0;
    const footColor = footCfg.color || body;
    const footLen = (footCfg.length != null ? parseFloat(footCfg.length) : 0.30) * radius;
    const flutes = parseInt(cosmetics.flutes != null ? cosmetics.flutes : 18, 10);
    const ringR = radius * 0.96;
    const bodyR = radius * (showRing ? 0.72 : 0.86);
    const lobeAmp = bodyR * 0.07;
    const capR = bodyR * 0.65;
    const rad = angle * Math.PI / 180;
    const STEPS = flutes * 8;
    const bodyPts = [];
    for (let i = 0; i < STEPS; i++) {
        const t = (i / STEPS) * 2 * Math.PI;
        const r = bodyR + lobeAmp * Math.cos(flutes * (t - rad));
        bodyPts.push(`${center + r * Math.cos(t)},${center - r * Math.sin(t)}`);
    }
    const bodyPoly = bodyPts.join(' ');
    const lOuterR = bodyR + lobeAmp;
    const lInnerR = bodyR - lobeAmp * 1.2;
    const lx1 = center + lInnerR * Math.cos(rad), ly1 = center - lInnerR * Math.sin(rad);
    const lx2 = center + lOuterR * Math.cos(rad), ly2 = center - lOuterR * Math.sin(rad);
    const winRad = winPos * Math.PI / 180;
    const wsx = Math.sin(winRad), wsy = -Math.cos(winRad);
    return (
        <g className="knob-cap-system british">
            <defs>
                <radialGradient id={`br-${filterId}`} cx="40%" cy="35%" r="78%">
                    <stop offset="0%" stopColor={shadeHex(body, 0.20)} />
                    <stop offset="55%" stopColor={body} />
                    <stop offset="100%" stopColor={shadeHex(body, -0.42)} />
                </radialGradient>
                <radialGradient id={`brcap-${filterId}`} cx="40%" cy="35%" r="78%">
                    <stop offset="0%" stopColor={shadeHex(capColor, 0.22)} />
                    <stop offset="55%" stopColor={capColor} />
                    <stop offset="100%" stopColor={shadeHex(capColor, -0.30)} />
                </radialGradient>
                <radialGradient id={`brring-${filterId}`} cx="40%" cy="35%" r="78%">
                    <stop offset="0%" stopColor={shadeHex(ringColor, 0.22)} />
                    <stop offset="60%" stopColor={ringColor} />
                    <stop offset="100%" stopColor={shadeHex(ringColor, -0.35)} />
                </radialGradient>
            </defs>
            {showRing && (
                <g pointerEvents="none">
                    <circle cx={center} cy={center} r={ringR} fill={`url(#brring-${filterId})`} stroke="#5a5e63" strokeWidth="1" filter={`url(#sh-${filterId})`} />
                    {[...Array(72)].map((_, j) => {
                        const t = (j / 72) * 2 * Math.PI;
                        const ri = bodyR + (ringR - bodyR) * 0.45, ro = ringR - 2;
                        return <line key={j}
                            x1={center + ri * Math.cos(t)} y1={center - ri * Math.sin(t)}
                            x2={center + ro * Math.cos(t)} y2={center - ro * Math.sin(t)}
                            stroke={shadeHex(ringColor, -0.45)} strokeWidth="0.7" opacity="0.7" />;
                    })}
                    {showWindow && (
                        <line x1={center + (bodyR + 2) * wsx} y1={center + (bodyR + 2) * wsy}
                              x2={center + (ringR - 2) * wsx} y2={center + (ringR - 2) * wsy}
                              stroke={winColor} strokeWidth={Math.max(2, radius * 0.04)} strokeLinecap="round" />
                    )}
                </g>
            )}
            {/* "British chicken" SHARP V-pointer foot — true triangle protruding
                from the body edge at the value angle (matches image 61 closely).
                Rotates with the value; a thin V-groove sits on top for definition. */}
            {showFoot && (() => {
                const perp = rad + Math.PI / 2;
                const baseR = bodyR + lobeAmp - 1;
                const tipR = baseR + footLen;
                const hwBase = bodyR * 0.32;
                const ox = center + tipR * Math.cos(rad), oy = center - tipR * Math.sin(rad);
                const b1x = center + baseR * Math.cos(rad) + hwBase * Math.cos(perp);
                const b1y = center - baseR * Math.sin(rad) - hwBase * Math.sin(perp);
                const b2x = center + baseR * Math.cos(rad) - hwBase * Math.cos(perp);
                const b2y = center - baseR * Math.sin(rad) + hwBase * Math.sin(perp);
                const tri = `${ox},${oy} ${b1x},${b1y} ${b2x},${b2y}`;
                // V-groove: two thin lines from the tip toward the body, marking the V detail.
                const gMx = center + (baseR + footLen * 0.20) * Math.cos(rad);
                const gMy = center - (baseR + footLen * 0.20) * Math.sin(rad);
                const gAx = b1x * 0.5 + ox * 0.5, gAy = b1y * 0.5 + oy * 0.5;
                const gBx = b2x * 0.5 + ox * 0.5, gBy = b2y * 0.5 + oy * 0.5;
                return (<>
                    <polygon points={tri} fill="#0a0a0a" transform={`translate(${DEPTH_OFFSET}, ${DEPTH_OFFSET})`} />
                    <polygon points={tri} fill={footColor} stroke={shadeHex(footColor, -0.55)} strokeWidth="1" strokeLinejoin="round" filter={`url(#sh-${filterId})`} />
                    {/* subtle V-groove engraving on top of the foot */}
                    <line x1={gMx} y1={gMy} x2={gAx} y2={gAy} stroke={shadeHex(footColor, -0.6)} strokeWidth="0.8" strokeLinecap="round" opacity="0.75" />
                    <line x1={gMx} y1={gMy} x2={gBx} y2={gBy} stroke={shadeHex(footColor, -0.6)} strokeWidth="0.8" strokeLinecap="round" opacity="0.75" />
                </>);
            })()}

            <g transform={`translate(${DEPTH_OFFSET}, ${DEPTH_OFFSET})`}>
                <polygon points={bodyPoly} fill="#000" strokeLinejoin="round" />
            </g>
            <g transform={`translate(${-DEPTH_OFFSET}, -${DEPTH_OFFSET})`} filter={`url(#sh-${filterId})`}>
                <polygon points={bodyPoly} fill={`url(#br-${filterId})`} stroke={shadeHex(body, -0.55)} strokeWidth="1" strokeLinejoin="round" />
                {showCap && (<>
                    <circle cx={center} cy={center} r={capR} fill={`url(#brcap-${filterId})`} stroke={shadeHex(capColor, -0.4)} strokeWidth="1" />
                    <g pointerEvents="none">
                        {[...Array(48)].map((_, j) => {
                            const t = (j / 48) * 2 * Math.PI;
                            const op = 0.05 + 0.10 * (0.5 + 0.5 * Math.sin(j * 2.3));
                            return <line key={j} x1={center} y1={center}
                                x2={center + capR * Math.cos(t)} y2={center - capR * Math.sin(t)}
                                stroke="#ffffff" strokeWidth="0.6" opacity={op} />;
                        })}
                    </g>
                </>)}
                <clipPath id={`capclip-${filterId}`}><polygon points={bodyPoly} /></clipPath>
                <g pointerEvents="none" clipPath={`url(#capclip-${filterId})`}>
                    <ellipse cx={center - bodyR * 0.30} cy={center - bodyR * 0.40} rx={bodyR * 0.55} ry={bodyR * 0.26} fill="white" opacity="0.16" filter={`url(#blur-${filterId})`} />
                </g>
                <line x1={lx1} y1={ly1} x2={lx2} y2={ly2} stroke="#ffffff" strokeWidth={Math.max(2, radius * 0.045)} strokeLinecap="round" />
            </g>
        </g>
    );
};
window.KnobCapBritish = KnobCapBritish;
