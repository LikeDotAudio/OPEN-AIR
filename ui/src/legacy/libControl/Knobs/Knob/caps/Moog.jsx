/**
 * Header: Moog.jsx
 * Purpose: Moog component or utility.
 * Description: Handles logic and rendering for Moog component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// Knob/caps/Moog.jsx — Minimoog/Voyager-style knob cap.
// Distinctive lathe-turned polished cap with CONCENTRIC RING GROOVES, on a
// cylindrical body that may be FLUTED (knurled) or SMOOTH. Plus optional
// flange skirt and optional chicken-foot pointer tab. Indicator is either a
// classic Moog DOT on the body edge or a white LINE.
//
// Config:
//   cosmetics.cap.{show, color, rings}            polished top + concentric rings (default show=true, rings=8)
//   cosmetics.flutes.{show, count}                vertical body knurl (default show=true, count=36)
//   cosmetics.flange.{show, color, size}          wide skirt behind the body
//   cosmetics.foot.{show, color}                  chicken-foot pointer tab at the body edge
//   cosmetics.indicator.{style, color}            'dot' (default, Moog classic) or 'line'
//   cosmetics.styling.fill_color | colors.primary body colour
const KnobCapMoog = ({ center, radius, angle, config, filterId, indicatorColor }) => {
    const DEPTH_OFFSET = 1.5;
    const shadeHex = window.shadeHex;
    const c = config || {};
    const cosmetics = c.cosmetics || {};
    const styling = cosmetics.styling || {};
    const colors = cosmetics.colors || {};

    const body = styling.fill_color || colors.primary || '#1c1c1c';
    const capColor = colors.cap || (cosmetics.cap && cosmetics.cap.color) || styling.cap_color || '#cfd2d6';

    const flutesCfg = cosmetics.flutes || {};
    const showFlutes = flutesCfg.show !== false;
    const fluteCount = parseInt(flutesCfg.count != null ? flutesCfg.count : 36, 10);

    const capCfg = cosmetics.cap || {};
    const showCap = capCfg.show !== false;
    const ringCount = parseInt(capCfg.rings != null ? capCfg.rings : 8, 10);

    const flangeCfg = cosmetics.flange || {};
    const showFlange = !!flangeCfg.show;
    const flangeR = (flangeCfg.size != null ? parseFloat(flangeCfg.size) : 0.94) * radius;
    const flangeColor = flangeCfg.color || body;

    const footCfg = cosmetics.foot || {};
    const showFoot = !!footCfg.show;
    const footColor = footCfg.color || body;

    const indCfg = cosmetics.indicator || {};
    const indStyle = (indCfg.style || 'dot').toLowerCase();
    const indColor = indCfg.color || '#ffffff';

    const bodyR = radius * (showFlange ? 0.66 : 0.80);
    const capR = bodyR * 0.70;
    const rad = angle * Math.PI / 180;

    return (
        <g className="knob-cap-system moog">
            <defs>
                <linearGradient id={`mg-${filterId}`} x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor={shadeHex(body, 0.18)} />
                    <stop offset="55%" stopColor={body} />
                    <stop offset="100%" stopColor={shadeHex(body, -0.42)} />
                </linearGradient>
                <radialGradient id={`mgcap-${filterId}`} cx="40%" cy="35%" r="78%">
                    <stop offset="0%" stopColor={shadeHex(capColor, 0.25)} />
                    <stop offset="55%" stopColor={capColor} />
                    <stop offset="100%" stopColor={shadeHex(capColor, -0.30)} />
                </radialGradient>
                <radialGradient id={`mgfl-${filterId}`} cx="40%" cy="35%" r="78%">
                    <stop offset="0%" stopColor={shadeHex(flangeColor, 0.20)} />
                    <stop offset="60%" stopColor={flangeColor} />
                    <stop offset="100%" stopColor={shadeHex(flangeColor, -0.45)} />
                </radialGradient>
            </defs>

            {/* Flange (optional) — drawn first, behind everything */}
            {showFlange && (
                <circle cx={center} cy={center} r={flangeR} fill={`url(#mgfl-${filterId})`} stroke={shadeHex(flangeColor, -0.55)} strokeWidth="1" filter={`url(#sh-${filterId})`} />
            )}

            {/* Chicken-foot pointer tab (optional) at the value angle */}
            {showFoot && (() => {
                const perp = rad + Math.PI / 2;
                const fHW = bodyR * 0.20, fOut = bodyR + radius * 0.22;
                const bx = center + (bodyR - 1) * Math.cos(rad), by = center - (bodyR - 1) * Math.sin(rad);
                const ox = center + fOut * Math.cos(rad), oy = center - fOut * Math.sin(rad);
                const pts = [
                    `${bx + fHW * Math.cos(perp)},${by - fHW * Math.sin(perp)}`,
                    `${ox + fHW * 0.6 * Math.cos(perp)},${oy - fHW * 0.6 * Math.sin(perp)}`,
                    `${ox - fHW * 0.6 * Math.cos(perp)},${oy + fHW * 0.6 * Math.sin(perp)}`,
                    `${bx - fHW * Math.cos(perp)},${by + fHW * Math.sin(perp)}`,
                ].join(' ');
                return <polygon points={pts} fill={footColor} stroke={shadeHex(footColor, -0.5)} strokeWidth="0.5" strokeLinejoin="round" />;
            })()}

            {/* Body depth offset */}
            <g transform={`translate(${DEPTH_OFFSET}, ${DEPTH_OFFSET})`}>
                <circle cx={center} cy={center} r={bodyR} fill="#000" />
            </g>

            {/* Body cylinder (fluted or smooth) + polished cap with concentric ridges */}
            <g transform={`translate(${-DEPTH_OFFSET}, -${DEPTH_OFFSET})`} filter={`url(#sh-${filterId})`}>
                <circle cx={center} cy={center} r={bodyR} fill={`url(#mg-${filterId})`} stroke={shadeHex(body, -0.5)} strokeWidth="1" />

                {/* Vertical flutes around the body ring (between cap and body edge) */}
                {showFlutes && (
                    <g pointerEvents="none">
                        {[...Array(fluteCount)].map((_, j) => {
                            const t = (j / fluteCount) * 2 * Math.PI;
                            return <line key={j}
                                x1={center + (capR + 2) * Math.cos(t)} y1={center - (capR + 2) * Math.sin(t)}
                                x2={center + (bodyR - 1) * Math.cos(t)} y2={center - (bodyR - 1) * Math.sin(t)}
                                stroke={shadeHex(body, -0.55)} strokeWidth="0.8" opacity="0.75" />;
                        })}
                    </g>
                )}

                {/* Polished metal cap with CONCENTRIC RING GROOVES (the Moog signature) */}
                {showCap && (<>
                    <circle cx={center} cy={center} r={capR} fill={`url(#mgcap-${filterId})`} stroke={shadeHex(capColor, -0.4)} strokeWidth="1" />
                    <g pointerEvents="none">
                        {[...Array(ringCount)].map((_, j) => {
                            const rr = capR * (1 - (j + 1) / (ringCount + 1));
                            return <circle key={j} cx={center} cy={center} r={rr} fill="none"
                                stroke={shadeHex(capColor, -0.32)} strokeWidth="0.5" opacity="0.55" />;
                        })}
                    </g>
                    {/* tiny centre pip (lathe centre mark) */}
                    <circle cx={center} cy={center} r={Math.max(0.8, capR * 0.04)} fill={shadeHex(capColor, -0.5)} opacity="0.8" />
                    {/* soft top-left glint clipped to the cap */}
                    <clipPath id={`mgcapclip-${filterId}`}>
                        <circle cx={center} cy={center} r={capR} />
                    </clipPath>
                    <g pointerEvents="none" clipPath={`url(#mgcapclip-${filterId})`}>
                        <ellipse cx={center - capR * 0.30} cy={center - capR * 0.40} rx={capR * 0.55} ry={capR * 0.28} fill="white" opacity="0.22" filter={`url(#blur-${filterId})`} />
                    </g>
                </>)}

                {/* Indicator: classic Moog DOT on body edge, or a LINE on the front flute */}
                {indStyle === 'line' ? (
                    <line x1={center + capR * Math.cos(rad)} y1={center - capR * Math.sin(rad)}
                          x2={center + (bodyR - 2) * Math.cos(rad)} y2={center - (bodyR - 2) * Math.sin(rad)}
                          stroke={indColor} strokeWidth={Math.max(2, radius * 0.04)} strokeLinecap="round" />
                ) : (
                    <circle cx={center + (bodyR * 0.88) * Math.cos(rad)}
                            cy={center - (bodyR * 0.88) * Math.sin(rad)}
                            r={Math.max(1.5, radius * 0.045)} fill={indColor} stroke="#000" strokeWidth="0.3" />
                )}
            </g>
        </g>
    );
};
window.KnobCapMoog = KnobCapMoog;
