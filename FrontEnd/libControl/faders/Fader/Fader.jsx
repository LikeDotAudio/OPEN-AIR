/**
 * Header: Fader.jsx
 * Purpose: Fader component or utility.
 * Description: Handles logic and rendering for Fader component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// Fader Component
// Author: Gemini (Collaborator)
// Version: 20260505.1700.2
//
// Description: High-fidelity React Fader component, respecting dynamic JSON configuration and inferring orientation.

// Inline comment: Logic for clamp
const clamp = (val, min, max) => Math.max(min, Math.min(max, val));

// Inline comment: Logic for Fader
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
    const width = config?.geometry?.width || config?.layout?.width || 60;
    const height = config?.geometry?.height || config?.layout?.height || 250;
    
    // Orientation Inference: check style.orientation, then fallback to geometry ratio
    const orientation = config?.style?.orientation || (width > height ? 'horizontal' : 'vertical');

    // Dimensions
    const trackSlotWidth = 10;
    const paddingStart = 25;
    const paddingEnd = 20;
    const totalLength = orientation === 'vertical' ? height : width;
    const range = max - min; // The fader range (value)
    const faderRange = totalLength - paddingStart - paddingEnd; // The fader range (pixels)

    const [isDragging, setIsDragging] = React.useState(false);
    const [localVal, setLocalVal] = React.useState(null);
    const dwellTimerRef = React.useRef(null);
    const containerRef = React.useRef(null);

    const displayValue = localVal !== null ? localVal : currentValue;

    const handleInteraction = (e) => {
        if (!containerRef.current) return;
        const rect = containerRef.current.getBoundingClientRect();
        
        let normPos = 0;
        if (orientation === 'vertical') {
            normPos = 1 - ((e.clientY - (rect.top + paddingStart)) / faderRange);
        } else {
            normPos = (e.clientX - (rect.left + paddingStart)) / faderRange;
        }
        
        const boundedNorm = clamp(normPos, 0, 1);
        const newValue = min + boundedNorm * range;
        const rounded = Math.round((newValue) * 100) / 100;
        setLocalVal(rounded);
        setCurrentValue(rounded);
    };

    const handlePointerDown = (e) => {
        setIsDragging(true);
        handleInteraction(e);
        clearTimeout(dwellTimerRef.current);
        if (containerRef.current) containerRef.current.setPointerCapture(e.pointerId);
    };

    const handlePointerMove = (e) => { if (isDragging) handleInteraction(e); };

    const handlePointerUp = (e) => {
        setIsDragging(false);
        if (containerRef.current) containerRef.current.releasePointerCapture(e.pointerId);
        clearTimeout(dwellTimerRef.current);
        dwellTimerRef.current = setTimeout(() => setLocalVal(null), 500);
    };

    const norm = (displayValue - min) / (max - min);
    const pos = clamp(norm, 0, 1) * faderRange;

    const containerStyle = { width, height, touchAction: 'none' };
    
    // SVG coordinates
    const trackX = orientation === 'vertical' ? (width/2 - trackSlotWidth/2) : paddingStart;
    const trackY = orientation === 'vertical' ? paddingStart : (height/2 - trackSlotWidth/2);
    const trackW = orientation === 'vertical' ? trackSlotWidth : faderRange;
    const trackH = orientation === 'vertical' ? range : trackSlotWidth;

    const thumbSize = 40;
    const thumbX = orientation === 'vertical' ? (width/2 - thumbSize/2) : (paddingStart + pos - thumbSize/2);
    const thumbY = orientation === 'vertical' ? (height - paddingEnd - pos - thumbSize/2) : (height/2 - thumbSize/2);

    return (
        <svg ref={containerRef} style={containerStyle} onPointerDown={handlePointerDown} onPointerMove={handlePointerMove} onPointerUp={handlePointerUp}>
            <rect width="100%" height="100%" fill="#2b2b2b" />
            <rect x={trackX} y={trackY} width={trackW} height={trackH} fill="#050505" stroke="#222" />
            
            <g transform={`translate(${thumbX}, ${thumbY})`}>
                <rect width={orientation === 'vertical' ? thumbSize : thumbSize/1.5} 
                      height={orientation === 'vertical' ? thumbSize/1.5 : thumbSize} 
                      fill="#dcdcdc" rx="4" stroke="#555" />
                <line x1={orientation === 'vertical' ? 10 : 15} y1={orientation === 'vertical' ? 15 : 10} 
                      x2={orientation === 'vertical' ? thumbSize-10 : 25} y2={orientation === 'vertical' ? 15 : 30} stroke="#333" strokeWidth="2" />
            </g>
        </svg>
    );
};

window.Fader = Fader;
