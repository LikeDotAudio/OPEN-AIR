// Fader Interaction Hook
// Author: Gemini (Collaborator)
// Version: 20260505.1700.1
//
// Description: Hook for managing fader pointer interactions.

const useFaderInteraction = (containerRef, orientation, min, max, faderRange, setCurrentValue, setIsDragging) => {
    const startYRef = React.useRef(0);
    const startValRef = React.useRef(0);

    const handleInteraction = (e) => {
        if (!containerRef.current) return;
        const rect = containerRef.current.getBoundingClientRect();
        
        let normPos = 0;
        if (orientation === 'vertical') {
            normPos = 1 - ((e.clientY - (rect.top + 25)) / faderRange);
        } else {
            normPos = (e.clientX - (rect.left + 25)) / faderRange;
        }
        
        const boundedNorm = window.FaderUtils.clamp(normPos, 0, 1);
        const newValue = min + boundedNorm * (max - min);
        setCurrentValue(Math.round((newValue) * 100) / 100);
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

    return { handlePointerDown, handlePointerMove, handlePointerUp };
};
