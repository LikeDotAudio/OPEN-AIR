// Knob/caps/Fender.jsx — orchestrator-level renderer for the FENDER (Strat)
// style. Inverted from a normal knob: the FACE rotates (knurl + ticks + numbers)
// while a FIXED reference pointer marks the value. Only the static gradients
// and drop shadow stay put; the rotating layer is pointer-transparent so the
// knob still drags cleanly.
//
// Receives orchestrator state as props (because it needs the SVG/handlers).
const KnobCapFender = (props) => {
    const {
        center, radius, norm, min, max, config, filterId, indicatorColor,
        size, fluid, wrapRef, svgRef,
        onPointerDown, onPointerMove, onPointerUp,
    } = props;
    const shadeHex = window.shadeHex;
    const c = config || {};
    const cosmetics = c.cosmetics || {};
    const styling = cosmetics.styling || {};
    const colors = cosmetics.colors || {};
    const sweep = (cosmetics.scale?.sweep ?? c.sweep ?? 300);
    const ptrPos = (cosmetics.pointer?.position || c.pointer_position || c.fender_pointer || 'top').toLowerCase();
    const sigP = ptrPos === 'right' ? 90 : ptrPos === 'bottom' ? 180 : ptrPos === 'left' ? 270 : 0;
    const N = Math.max(2, Math.round(cosmetics.scale?.count ?? 11));
    const body = styling.fill_color || colors.primary || '#eeeeee';
    const numColor = colors.text || styling.tick_color || '#caa44a';
    const gTop = shadeHex(body, 0.24), gBot = shadeHex(body, -0.34);
    const skirtR = radius * 0.97, ringR = radius * 0.66, bodyR = radius * 0.54, rNum = radius * 0.82;
    const _numFontCfg = cosmetics.scale?.text_size ?? cosmetics.scale?.font_size ?? c.number_size ?? null;
    const numFont = (_numFontCfg != null) ? parseFloat(_numFontCfg) : Math.max(11, radius * 0.195);
    const faceRot = -norm * sweep;
    const sxp = (sig, r) => center + r * Math.sin(sig * Math.PI / 180);
    const syp = (sig, r) => center - r * Math.cos(sig * Math.PI / 180);
    const marks = [];
    for (let k = 0; k < N; k++) {
        const nk = (N > 1) ? k / (N - 1) : 0;
        const vk = min + nk * (max - min), sig = sigP + nk * sweep;
        marks.push(<line key={'t' + k} x1={sxp(sig, skirtR * 0.88)} y1={syp(sig, skirtR * 0.88)} x2={sxp(sig, skirtR * 0.96)} y2={syp(sig, skirtR * 0.96)} stroke={numColor} strokeWidth={1.5} strokeLinecap="round" />);
        marks.push(<text key={'n' + k} x={sxp(sig, rNum)} y={syp(sig, rNum)} fill={numColor} fontSize={numFont} fontFamily="Arial" fontWeight="bold" textAnchor="middle" dominantBaseline="central">{Math.round(vk)}</text>);
    }
    const ribs = [], M = 48;
    for (let j = 0; j < M; j++) {
        const sig = j * 360 / M;
        ribs.push(<line key={'r' + j} x1={sxp(sig, bodyR)} y1={syp(sig, bodyR)} x2={sxp(sig, ringR)} y2={syp(sig, ringR)} stroke={shadeHex(body, -0.5)} strokeWidth={1} opacity="0.5" />);
    }
    const pr0 = skirtR + 2, pr1 = skirtR - radius * 0.16, pw = radius * 0.07, sr = sigP * Math.PI / 180;
    const ptr = `${sxp(sigP, pr1)},${syp(sigP, pr1)} `
        + `${center + pr0 * Math.sin(sr) + pw * Math.cos(sr)},${center - pr0 * Math.cos(sr) + pw * Math.sin(sr)} `
        + `${center + pr0 * Math.sin(sr) - pw * Math.cos(sr)},${center - pr0 * Math.cos(sr) - pw * Math.sin(sr)}`;
    return (
        <div ref={wrapRef} style={{ width: fluid ? '100%' : size, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <svg ref={svgRef} width={size} height={size} viewBox={`0 0 ${size} ${size}`}
            style={{ touchAction: 'none', cursor: 'ns-resize', overflow: 'visible', userSelect: 'none' }}
            onPointerDown={onPointerDown} onPointerMove={onPointerMove}
            onPointerUp={onPointerUp} onPointerCancel={onPointerUp}>
            <defs>
                <radialGradient id={`fskirt-${filterId}`} cx="42%" cy="38%" r="72%">
                    <stop offset="0%" stopColor={shadeHex(body, 0.16)} /><stop offset="72%" stopColor={body} /><stop offset="100%" stopColor={shadeHex(body, -0.30)} />
                </radialGradient>
                <radialGradient id={`fbody-${filterId}`} cx="40%" cy="35%" r="75%">
                    <stop offset="0%" stopColor={gTop} /><stop offset="60%" stopColor={body} /><stop offset="100%" stopColor={gBot} />
                </radialGradient>
                <filter id={`sh-${filterId}`} x="-50%" y="-50%" width="200%" height="200%">
                    <feDropShadow dx="2" dy="2" stdDeviation="3" floodColor="#000" floodOpacity="0.5"/>
                </filter>
                <filter id={`blur-${filterId}`}><feGaussianBlur stdDeviation="2" /></filter>
            </defs>
            <circle cx={center} cy={center} r={skirtR} fill={`url(#fskirt-${filterId})`} stroke="#222" strokeWidth="1" filter={`url(#sh-${filterId})`} pointerEvents="none" />
            <g transform={`rotate(${faceRot} ${center} ${center})`} pointerEvents="none">
                {ribs}
                {marks}
            </g>
            <ellipse cx={center} cy={center + radius * 0.02} rx={bodyR * 1.0} ry={bodyR * 0.18} fill="#000" opacity="0.35" filter={`url(#blur-${filterId})`} pointerEvents="none" />
            <g pointerEvents="none" transform={`translate(0 ${-radius * 0.07})`}>
                <circle cx={center} cy={center} r={bodyR} fill={`url(#fbody-${filterId})`} stroke={shadeHex(body, -0.4)} strokeWidth="1" />
                <ellipse cx={center - bodyR * 0.32} cy={center - bodyR * 0.4} rx={bodyR * 0.5} ry={bodyR * 0.26} fill="white" opacity="0.16" filter={`url(#blur-${filterId})`} />
            </g>
            <polygon points={ptr} fill={indicatorColor} stroke="#000" strokeWidth="0.5" pointerEvents="none" />
        </svg>
        </div>
    );
};
window.KnobCapFender = KnobCapFender;
