// DualFader Component
// Author: Gemini (Collaborator)
// Version: 20260525.1200.0
//
// Description: Two caps share ONE rail (stacked along a single track, like the
// Python `fader_dual`), with a coloured delta line drawn between them — NOT two
// separate side-by-side rails. Caps keep distinct colours so they're still
// tellable apart while overlapping. Drag grabs the nearest cap.

const clamp = (val, min, max) => Math.max(min, Math.min(max, val));

const DualFader = ({ value, onChange, config }) => {
    const min = config?.domain?.primary?.min !== undefined ? config.domain.primary.min : 0;
    const max = config?.domain?.primary?.max !== undefined ? config.domain.primary.max : 100;

    const width = config?.geometry?.width || config?.layout?.width || 80;
    const height = config?.geometry?.height || config?.layout?.height || 250;
    const orientation = config?.style?.orientation || config?.geometry?.orientation
        || (width > height ? 'horizontal' : 'vertical');
    const isVert = orientation === 'vertical';

    // Colours: caps stay distinct (blue/orange) so the two handles are tellable
    // apart on the shared rail; the delta line uses the accent/highlight colour.
    const colors = config?.cosmetics?.colors || {};
    const cap1Color = colors.primary || config?.cap_color_1 || '#33A1FD';
    const cap2Color = colors.secondary || config?.cap_color_2 || '#FF8C00';
    const deltaColor = colors.accent || config?.value_highlight_color || '#f4902c';
    const showValues = config?.cosmetics?.style_overrides?.value_follow !== false;

    const topRes = 25, botRes = 20;
    const capW = 34, capH = 44;
    const padding = capH / 2;

    const travelHeight = height - topRes - botRes - 2 * padding;
    const travelWidth = width - topRes - botRes - 2 * padding;
    const travelLen = isVert ? travelHeight : travelWidth;

    // value may arrive as [v1, v2]; otherwise fall back to per-handle defaults.
    const dv1 = config?.domain?.primary?.value_default_v1;
    const dv2 = config?.domain?.primary?.value_default_v2;
    const _n = (v, d) => { const n = parseFloat(v); return Number.isFinite(n) ? n : d; };
    const val1 = Array.isArray(value) ? _n(value[0], min)
        : (typeof value === 'object' && value ? _n(value.val1, _n(dv1, min)) : _n(dv1, min));
    const val2 = Array.isArray(value) ? _n(value[1], min)
        : (typeof value === 'object' && value ? _n(value.val2, _n(dv2, min)) : _n(dv2, min));

    const [isDragging, setIsDragging] = React.useState(null);
    const containerRef = React.useRef(null);

    const getPos = (v) => clamp((v - min) / (max - min || 1), 0, 1) * travelLen;
    const pos1 = getPos(val1), pos2 = getPos(val2);
    // Pixel position ALONG the rail. Both caps sit on the same centre line (cross).
    const capPos1 = isVert ? travelHeight - pos1 + topRes + padding : pos1 + topRes + padding;
    const capPos2 = isVert ? travelHeight - pos2 + topRes + padding : pos2 + topRes + padding;
    const cross = isVert ? width / 2 : height / 2;

    const valueFromEvent = (e) => {
        const rect = containerRef.current.getBoundingClientRect();
        const scaleY = rect.height / (containerRef.current.offsetHeight || 1);
        const scaleX = rect.width / (containerRef.current.offsetWidth || 1);
        const norm = isVert
            ? 1 - (((e.clientY - rect.top) / scaleY) - topRes - padding) / travelHeight
            : (((e.clientX - rect.left) / scaleX) - topRes - padding) / travelWidth;
        return Math.round((min + clamp(norm, 0, 1) * (max - min)) * 100) / 100;
    };

    const apply = (e, which) => {
        if (!containerRef.current || !which) return;
        const nv = valueFromEvent(e);
        onChange(which === 'fader1' ? [nv, val2] : [val1, nv]);
    };

    // Pick the NEAREST cap to the click so overlapping handles are both reachable.
    const handlePointerDown = (e) => {
        if (!containerRef.current) return;
        const rect = containerRef.current.getBoundingClientRect();
        const scaleY = rect.height / (containerRef.current.offsetHeight || 1);
        const scaleX = rect.width / (containerRef.current.offsetWidth || 1);
        const coord = isVert ? ((e.clientY - rect.top) / scaleY) : ((e.clientX - rect.left) / scaleX);
        const id = Math.abs(coord - capPos1) <= Math.abs(coord - capPos2) ? 'fader1' : 'fader2';
        setIsDragging(id);
        apply(e, id);
        containerRef.current.setPointerCapture(e.pointerId);
    };
    const handlePointerMove = (e) => { if (isDragging) apply(e, isDragging); };
    const handlePointerUp = (e) => {
        setIsDragging(null);
        if (containerRef.current) containerRef.current.releasePointerCapture(e.pointerId);
    };

    const FaderCap = window.FaderCap;
    const renderCap = (pos, color, id) => (
        <div style={{
            position: 'absolute',
            left: isVert ? cross : pos,
            top: isVert ? pos : cross,
            width: isVert ? capW : capH,
            height: isVert ? capH : capW,
            transform: 'translate(-50%, -50%)',
            pointerEvents: 'none',  // the container owns the drag (nearest-cap pick)
            zIndex: isDragging === id ? 10 : 5,
        }}>
            {FaderCap && <FaderCap width={capW} height={capH} capColor={color} orientation={orientation} />}
        </div>
    );

    // Delta line spans between the two caps along the rail.
    const dMin = Math.min(capPos1, capPos2), dLen = Math.abs(capPos1 - capPos2);
    const labelText = typeof config?.label_active === 'string' ? config.label_active
        : (config?.label_active?.En || (typeof config?.label === 'string' ? config.label : ''));

    return (
        <div ref={containerRef}
            style={{
                width, height, position: 'relative',
                backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, '#2b2b2b') : '#2b2b2b'),
                touchAction: 'none', overflow: 'hidden', borderRadius: 4, cursor: 'pointer'
            }}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
        >
            {labelText && (
                <div style={{ position: 'absolute', top: 4, left: 0, width: '100%', textAlign: 'center', color: '#fff', fontSize: 9, fontWeight: 'bold', pointerEvents: 'none' }}>{labelText}</div>
            )}

            {/* Single shared rail (centre line) */}
            <div style={{
                position: 'absolute',
                left: isVert ? cross : (topRes + padding - 5),
                top: isVert ? (topRes + padding - 5) : cross,
                width: isVert ? 10 : travelWidth + 10,
                height: isVert ? travelHeight + 10 : 10,
                transform: isVert ? 'translateX(-50%)' : 'translateY(-50%)',
                background: '#0a0a0a', border: '1px solid #333', borderRadius: 3,
            }} />

            {/* Delta line between the two caps */}
            <div style={{
                position: 'absolute',
                left: isVert ? cross : dMin,
                top: isVert ? dMin : cross,
                width: isVert ? 4 : dLen,
                height: isVert ? dLen : 4,
                transform: isVert ? 'translateX(-50%)' : 'translateY(-50%)',
                background: deltaColor, borderRadius: 2, pointerEvents: 'none', zIndex: 4,
            }} />

            {renderCap(capPos1, cap1Color, 'fader1')}
            {renderCap(capPos2, cap2Color, 'fader2')}

            {/* Value labels beside each cap */}
            {showValues && (<>
                <div style={{ position: 'absolute', left: isVert ? cross - 26 : capPos1, top: isVert ? capPos1 : cross - 26, transform: 'translate(-50%, -50%)', color: cap1Color, fontSize: 8, fontWeight: 'bold', pointerEvents: 'none', whiteSpace: 'nowrap' }}>{val1.toFixed(1)}</div>
                <div style={{ position: 'absolute', left: isVert ? cross + 26 : capPos2, top: isVert ? capPos2 : cross + 26, transform: 'translate(-50%, -50%)', color: cap2Color, fontSize: 8, fontWeight: 'bold', pointerEvents: 'none', whiteSpace: 'nowrap' }}>{val2.toFixed(1)}</div>
            </>)}

            {/* Delta readout */}
            <div style={{ position: 'absolute', right: 4, bottom: 3, color: '#aaa', fontSize: 8, fontWeight: 'bold', pointerEvents: 'none' }}>Δ {(val2 - val1).toFixed(2)}</div>
        </div>
    );
};

window.DualFader = DualFader;
