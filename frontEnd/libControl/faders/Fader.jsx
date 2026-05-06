// Fader Component
// Author: Gemini (Collaborator)
// Version: 20260505.1600.1
//
// Description: High-fidelity Fader component using SVG to achieve the desired industrial aesthetic.

const Fader = ({ value: externalValue, onChange, config, topic, nodeJson }) => {
    const min = config?.domain?.primary?.min !== undefined ? config.domain.primary.min : 0;
    const max = config?.domain?.primary?.max !== undefined ? config.domain.primary.max : 100;
    
    // MQTT integration
    const useMqtt = !!topic;
    const useMqttState = window.useMqttState;
    const [val, setVal] = useMqtt ? useMqttState(topic, externalValue || min, nodeJson) : [externalValue, onChange, 'En'];
    const currentValue = useMqtt ? val : (externalValue !== undefined ? externalValue : min);
    const setCurrentValue = useMqtt ? setVal : (val) => { if (onChange) onChange(val); };

    // Layout configuration
    const orientation = config?.style?.orientation || 'vertical'; 
    const width = config?.geometry?.width || 60;
    const height = config?.geometry?.height || 250;
    const thumbWidth = 40;
    const thumbHeight = 30;
    
    const paddingStart = 25;
    const paddingEnd = 20;
    const range = (orientation === 'vertical' ? height : width) - paddingStart - paddingEnd;
    const trackSlotWidth = 10;

    const [isDragging, setIsDragging] = React.useState(false);
    const containerRef = React.useRef(null);

    const handleInteraction = (e) => {
        if (!containerRef.current) return;
        const rect = containerRef.current.getBoundingClientRect();
        const pos = orientation === 'vertical' ? (rect.bottom - paddingEnd - e.clientY) : (e.clientX - rect.left - paddingStart);
        const norm = Math.max(0, Math.min(1, pos / range));
        setCurrentValue(Math.round((min + norm * (max - min)) * 100) / 100);
    };

    const handlePointerDown = (e) => {
        setIsDragging(true);
        handleInteraction(e);
        if (containerRef.current) containerRef.current.setPointerCapture(e.pointerId);
    };

    const handlePointerMove = (e) => { if (isDragging) handleInteraction(e); };

    const handlePointerUp = (e) => {
        setIsDragging(false);
        if (containerRef.current) containerRef.current.releasePointerCapture(e.pointerId);
    };

    const norm = (currentValue - min) / (max - min);
    const pos = norm * range;

    const containerStyle = { width, height, touchAction: 'none' };
    
    // SVG coordinates
    const trackX = orientation === 'vertical' ? (width/2 - trackSlotWidth/2) : paddingStart;
    const trackY = orientation === 'vertical' ? paddingStart : (height/2 - trackSlotWidth/2);
    const trackW = orientation === 'vertical' ? trackSlotWidth : range;
    const trackH = orientation === 'vertical' ? range : trackSlotWidth;

    const thumbX = orientation === 'vertical' ? (width/2 - thumbWidth/2) : (paddingStart + pos - thumbWidth/2);
    const thumbY = orientation === 'vertical' ? (height - paddingEnd - pos - thumbHeight/2) : (height/2 - thumbHeight/2);

    return (
        <svg ref={containerRef} style={containerStyle} onPointerDown={handlePointerDown} onPointerMove={handlePointerMove} onPointerUp={handlePointerUp}>
            {/* Background */}
            <rect width="100%" height="100%" fill="#2b2b2b" />
            
            {/* Track Slot */}
            <rect x={trackX} y={trackY} width={trackW} height={trackH} fill="#050505" stroke="#222" />
            
            {/* Thumb (Cap) */}
            <g transform={`translate(${thumbX}, ${thumbY})`}>
                <rect width={thumbWidth} height={thumbHeight} fill="#dcdcdc" rx="4" stroke="#555" />
                <line x1="10" y1={thumbHeight/2} x2={thumbWidth-10} y2={thumbHeight/2} stroke="#333" strokeWidth="2" />
                <line x1="10" y1={thumbHeight/2 - 4} x2={thumbWidth-10} y2={thumbHeight/2 - 4} stroke="#aaa" strokeWidth="1" />
            </g>
        </svg>
    );
};

window.Fader = Fader;