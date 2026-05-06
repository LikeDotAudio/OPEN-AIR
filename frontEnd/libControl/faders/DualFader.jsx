// DualFader Component
// Author: Gemini (Collaborator)
// Version: 20260505.1700.1
//
// Description: DualFader component, adapted for browser-safe module loading.

const clamp = (val, min, max) => Math.max(min, Math.min(max, val));

const DualFader = ({ value, onChange, config }) => {
    const min = config?.domain?.primary?.min !== undefined ? config.domain.primary.min : 0;
    const max = config?.domain?.primary?.max !== undefined ? config.domain.primary.max : 100;
    const orientation = config?.style?.orientation || 'vertical'; 
    const width = config?.geometry?.width || config?.layout?.width || 80;
    const height = config?.geometry?.height || config?.layout?.height || 150;

    const val1 = Array.isArray(value) ? value[0] : min;
    const val2 = Array.isArray(value) ? value[1] : min;

    const [isDragging, setIsDragging] = React.useState(null);
    const containerRef = React.useRef(null);

    const handleInteraction = (e) => {
        if (!containerRef.current) return;
        const rect = containerRef.current.getBoundingClientRect();
        const rangeLen = (orientation === 'vertical' ? height : width) - 40;
        
        let normPos = 0;
        if (orientation === 'vertical') {
            normPos = 1 - ((e.clientY - (rect.top + 20)) / rangeLen);
        } else {
            normPos = (e.clientX - (rect.left + 20)) / rangeLen;
        }
        
        const boundedNorm = clamp(normPos, 0, 1);
        const newVal = Math.round((min + boundedNorm * (max - min)) * 100) / 100;

        if (isDragging === 'fader1') onChange([newVal, val2]);
        else if (isDragging === 'fader2') onChange([val1, newVal]);
    };

    const handlePointerDown = (e) => {
        const classList = e.target.className || "";
        if (classList.includes('fader-cap-1')) setIsDragging('fader1');
        else if (classList.includes('fader-cap-2')) setIsDragging('fader2');
        else return;

        handleInteraction(e);
        if (containerRef.current) containerRef.current.setPointerCapture(e.pointerId);
    };

    const handlePointerMove = (e) => { if (isDragging) handleInteraction(e); };

    const handlePointerUp = (e) => {
        setIsDragging(null);
        if (containerRef.current) containerRef.current.releasePointerCapture(e.pointerId);
    };

    const pos1 = ((val1 - min) / (max - min)) * (orientation === 'vertical' ? height - 40 : width - 40);
    const pos2 = ((val2 - min) / (max - min)) * (orientation === 'vertical' ? height - 40 : width - 40);

    const containerStyle = { width, height, position: 'relative', backgroundColor: '#2b2b2b', touchAction: 'none' };
    const trackStyle = { position: 'absolute', backgroundColor: '#050505', border: '1px solid #222',
        left: orientation === 'vertical' ? (width/2 - 5) : 20,
        top: orientation === 'vertical' ? 20 : (height/2 - 5),
        width: orientation === 'vertical' ? 10 : width - 40,
        height: orientation === 'vertical' ? height - 40 : 10 };

    const thumbStyle = (pos, color, className) => ({
        position: 'absolute', backgroundColor: color, borderRadius: 4, border: '1px solid #555',
        width: orientation === 'vertical' ? 30 : 20, height: orientation === 'vertical' ? 20 : 30,
        left: orientation === 'vertical' ? (width/2 - 15) : (20 + pos - 10),
        top: orientation === 'vertical' ? (height - 20 - pos - 10) : (height/2 - 15),
        zIndex: 1,
    });

    return (
        <div ref={containerRef} style={containerStyle} onPointerDown={handlePointerDown} onPointerMove={handlePointerMove} onPointerUp={handlePointerUp}>
            <div style={trackStyle} />
            <div className="fader-cap-1" style={thumbStyle(pos1, '#33A1FD', 'fader-cap-1')} />
            <div className="fader-cap-2" style={thumbStyle(pos2, '#FF8C00', 'fader-cap-2')} />
        </div>
    );
};

window.DualFader = DualFader;
