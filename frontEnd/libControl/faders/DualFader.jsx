// DualFader Component
// Author: Gemini (Collaborator)
// Version: 20260505.1700.1
//
// Description: DualFader component, adapted for browser-safe module loading.

const clamp = (val, min, max) => Math.max(min, Math.min(max, val));

const DualFader = ({ value, onChange, config }) => {
    const min = config?.domain?.primary?.min !== undefined ? config.domain.primary.min : 0;
    const max = config?.domain?.primary?.max !== undefined ? config.domain.primary.max : 100;
    
    const width = config?.geometry?.width || config?.layout?.width || 80;
    const height = config?.geometry?.height || config?.layout?.height || 250;
    const orientation = config?.style?.orientation || (width > height ? 'horizontal' : 'vertical');

    const topRes = 25;
    const botRes = 20;
    const capW = 34;
    const capH = 44;
    const padding = capH / 2;

    const travelHeight = height - topRes - botRes - (2 * padding);
    const travelWidth = width - topRes - botRes - (2 * padding);
    const travelLen = orientation === 'vertical' ? travelHeight : travelWidth;

    const val1 = Array.isArray(value) ? value[0] : (typeof value === 'object' ? (value.val1 ?? min) : min);
    const val2 = Array.isArray(value) ? value[1] : (typeof value === 'object' ? (value.val2 ?? min) : min);

    const [isDragging, setIsDragging] = React.useState(null);
    const containerRef = React.useRef(null);

    const handleInteraction = (e) => {
        if (!containerRef.current) return;
        const rect = containerRef.current.getBoundingClientRect();
        
        let norm = 0;
        if (orientation === 'vertical') {
            const y = e.clientY - rect.top;
            norm = 1 - (y - topRes - padding) / travelHeight;
        } else {
            const x = e.clientX - rect.left;
            norm = (x - topRes - padding) / travelWidth;
        }
        
        const clampedNorm = Math.max(0, Math.min(1, norm));
        const newVal = Math.round((min + clampedNorm * (max - min)) * 100) / 100;

        if (isDragging === 'fader1') onChange([newVal, val2]);
        else if (isDragging === 'fader2') onChange([val1, newVal]);
    };

    const handlePointerDown = (e, id) => {
        setIsDragging(id);
        handleInteraction(e);
        if (containerRef.current) containerRef.current.setPointerCapture(e.pointerId);
    };

    const handlePointerMove = (e) => { if (isDragging) handleInteraction(e); };

    const handlePointerUp = (e) => {
        setIsDragging(null);
        if (containerRef.current) containerRef.current.releasePointerCapture(e.pointerId);
    };

    const getPos = (v) => {
        const norm = (v - min) / (max - min || 1);
        return Math.max(0, Math.min(1, norm)) * travelLen;
    };

    const pos1 = getPos(val1);
    const pos2 = getPos(val2);

    const capPos1 = orientation === 'vertical' ? travelHeight - pos1 + topRes + padding : pos1 + topRes + padding;
    const capPos2 = orientation === 'vertical' ? travelHeight - pos2 + topRes + padding : pos2 + topRes + padding;

    const FaderCap = window.FaderCap;

    const renderCap = (pos, color, id) => (
        <div 
            onPointerDown={(e) => handlePointerDown(e, id)}
            style={{
                position: 'absolute',
                left: orientation === 'vertical' ? (id === 'fader1' ? width/2 - 18 : width/2 + 18) : pos,
                top: orientation === 'vertical' ? pos : (id === 'fader1' ? height/2 - 18 : height/2 + 18),
                width: orientation === 'vertical' ? capW : capH,
                height: orientation === 'vertical' ? capH : capW,
                transform: 'translate(-50%, -50%)',
                cursor: 'pointer',
                zIndex: isDragging === id ? 10 : 5
            }}
        >
            {FaderCap && <FaderCap width={capW} height={capH} capColor={color} orientation={orientation} />}
        </div>
    );

    return (
        <div 
            ref={containerRef} 
            style={{ width, height, position: 'relative', backgroundColor: '#2b2b2b', touchAction: 'none', overflow: 'hidden', borderRadius: 4 }}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
        >
            {/* Split Tracks */}
            <div style={{
                position: 'absolute',
                left: orientation === 'vertical' ? width/2 - 18 - 4 : topRes + padding - 5,
                top: orientation === 'vertical' ? topRes + padding - 5 : height/2 - 18 - 4,
                width: orientation === 'vertical' ? 8 : travelWidth + 10,
                height: orientation === 'vertical' ? travelHeight + 10 : 8,
                background: '#050505', border: '1px solid #222', borderRadius: 2
            }} />
            <div style={{
                position: 'absolute',
                left: orientation === 'vertical' ? width/2 + 18 - 4 : topRes + padding - 5,
                top: orientation === 'vertical' ? topRes + padding - 5 : height/2 + 18 - 4,
                width: orientation === 'vertical' ? 8 : travelWidth + 10,
                height: orientation === 'vertical' ? travelHeight + 10 : 8,
                background: '#050505', border: '1px solid #222', borderRadius: 2
            }} />

            {renderCap(capPos1, '#33A1FD', 'fader1')}
            {renderCap(capPos2, '#FF8C00', 'fader2')}
            
            {/* Middle Divider */}
            <div style={{
                position: 'absolute',
                left: orientation === 'vertical' ? width/2 - 1 : 0,
                top: orientation === 'vertical' ? 0 : height/2 - 1,
                width: orientation === 'vertical' ? 2 : width,
                height: orientation === 'vertical' ? height : 2,
                background: '#444'
            }} />
        </div>
    );
};

window.DualFader = DualFader;
