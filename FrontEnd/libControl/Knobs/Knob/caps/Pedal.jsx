// Knob/caps/Pedal.jsx — guitar-pedal style knob cap.
// RECTANGULAR rounded body (taller along the pointer axis) with a RAISED
// pointer TAB on one end. Two shadow-generating features:
//   1. The body rectangle drops a shadow on the panel behind it.
//   2. The raised pointer tab drops a shadow on the body.
// A white indicator line runs down the centre from the body to the tab tip.
//
// Config:
//   cosmetics.line.{color,width}    (indicator line — default white, ~5% of radius)
//   cosmetics.tab.{size,length}     (pointer tab dims — defaults 0.55 / 0.30 of radius)
//   cosmetics.styling.fill_color | colors.primary  (body colour)
const KnobCapPedal = ({ center, radius, angle, config, filterId, indicatorColor }) => {
    const shadeHex = window.shadeHex;
    const c = config || {};
    const cosmetics = c.cosmetics || {};
    const styling = cosmetics.styling || {};
    const colors = cosmetics.colors || {};

    const body = styling.fill_color || colors.primary || '#43A047';
    const gTop = shadeHex(body, 0.22), gBot = shadeHex(body, -0.32);
    const lineColor = (cosmetics.line && cosmetics.line.color) || '#ffffff';
    const lineWidth = (cosmetics.line && cosmetics.line.width != null)
        ? parseFloat(cosmetics.line.width) : Math.max(2.5, radius * 0.06);
    const tabCfg = cosmetics.tab || {};
    const tabSize = (tabCfg.size != null) ? parseFloat(tabCfg.size) : 0.55;
    const tabLength = (tabCfg.length != null) ? parseFloat(tabCfg.length) : 0.30;

    // Geometry — drawn in LOCAL frame where the pointer points SCREEN UP, then
    // the whole group is rotated by (90 - angle) so the tall axis follows value.
    const bodyW = radius * 1.22;      // perpendicular to pointer axis
    const bodyH = radius * 1.45;      // along the pointer axis (taller)
    const cornerR = Math.min(bodyW, bodyH) * 0.20;
    const tabW = radius * tabSize;
    const tabH = radius * tabLength;
    const tabCornerR = tabW * 0.30;
    const rotDeg = 90 - angle;

    const bx = center - bodyW / 2, by = center - bodyH / 2;
    const tx = center - tabW / 2, ty = center - bodyH / 2 - tabH + 1;  // 1px overlap with body

    return (
        <g className="knob-cap-system pedal">
            <defs>
                <linearGradient id={`pd-${filterId}`} x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor={gTop} />
                    <stop offset="55%" stopColor={body} />
                    <stop offset="100%" stopColor={gBot} />
                </linearGradient>
                <linearGradient id={`pdtab-${filterId}`} x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor={shadeHex(body, 0.28)} />
                    <stop offset="100%" stopColor={shadeHex(body, 0.05)} />
                </linearGradient>
                {/* Drop shadow cast by the raised pointer tab onto the body */}
                <filter id={`pdtabsh-${filterId}`} x="-40%" y="-40%" width="180%" height="180%">
                    <feDropShadow dx="0.5" dy="2.5" stdDeviation="1.4" floodColor="#000" floodOpacity="0.55"/>
                </filter>
            </defs>

            <g transform={`rotate(${rotDeg} ${center} ${center})`}>
                {/* Body rectangle — drops a shadow on the panel via the shared `sh-` filter */}
                <rect x={bx} y={by} width={bodyW} height={bodyH} rx={cornerR} ry={cornerR}
                      fill={`url(#pd-${filterId})`} stroke={shadeHex(body, -0.5)} strokeWidth="1"
                      filter={`url(#sh-${filterId})`} />

                {/* Raised pointer TAB — drops its own shadow onto the body */}
                <rect x={tx} y={ty} width={tabW} height={tabH + cornerR + 2}
                      rx={tabCornerR} ry={tabCornerR}
                      fill={`url(#pdtab-${filterId})`} stroke={shadeHex(body, -0.5)} strokeWidth="1"
                      filter={`url(#pdtabsh-${filterId})`} />

                {/* Glint clipped to the body so it doesn't spill onto the tab */}
                <clipPath id={`pdclip-${filterId}`}>
                    <rect x={bx} y={by} width={bodyW} height={bodyH} rx={cornerR} ry={cornerR} />
                </clipPath>
                <g pointerEvents="none" clipPath={`url(#pdclip-${filterId})`}>
                    <ellipse cx={center - bodyW * 0.22} cy={center - bodyH * 0.32}
                             rx={bodyW * 0.30} ry={bodyH * 0.22}
                             fill="white" opacity="0.18" filter={`url(#blur-${filterId})`} />
                </g>

                {/* White indicator line from body centre to the tab tip */}
                <line x1={center} y1={center}
                      x2={center} y2={ty + tabCornerR}
                      stroke={lineColor} strokeWidth={lineWidth} strokeLinecap="round" />
            </g>
        </g>
    );
};
window.KnobCapPedal = KnobCapPedal;
