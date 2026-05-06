import React, { useState, useRef, useEffect } from 'react';
import './Fader.css'; // Assuming CSS for styling

// Helper function to map value to position considering log scale
const mapValueToPosition = (value, min, max, logExponent) => {
    const range = max - min;
    if (range === 0) return 0;
    const logVal = Math.log(value - min + 1) / logExponent;
    const logMin = Math.log(min - min + 1) / logExponent;
    const logMax = Math.log(max - min + 1) / logExponent;
    const logRange = logMax - logMin;
    if (logRange === 0) return 0;
    return (logVal - logMin) / logRange;
};

const DualFader = ({ value, onChange, config }) => {
    const min = config?.domain?.primary?.min !== undefined ? config.domain.primary.min : 0;
    const max = config?.domain?.primary?.max !== undefined ? config.domain.primary.max : 100;
    const logExponent = config?.domain?.primary?.log_exponent || 1.0;
    const orientation = config?.style?.orientation || 'vertical'; // 'vertical' or 'horizontal'
    
    const width = config?.geometry?.width || config?.layout?.width || 80;
    const height = config?.geometry?.height || config?.layout?.height || 150;

    const faderHeight = orientation === 'vertical' ? height : width;
    const faderWidth = orientation === 'vertical' ? width : height;

    // Extracting values for two faders
    const val1 = Array.isArray(value) ? value[0] : min;
    const val2 = Array.isArray(value) ? value[1] : min;

    // Styling and cosmetics
    const trackColor = config?.style?.track_color || '#444';
    const capColor1 = config?.style?.cap_color1 || config?.cosmetics?.colors?.primary || '#33A1FD';
    const capColor2 = config?.style?.cap_color2 || config?.cosmetics?.colors?.accent || '#FF8C00'; // Different color for second cap
    const pointerColor = config?.indicator_color || '#fff';
    const pointerWidth = config?.style?.pointer_width || 2;
    const pointerHeight = config?.style?.pointer_height || 15;
    const capWidth = config?.style?.cap_width || faderWidth * 0.4; // Width of the fader cap

    const boundedValue1 = Math.max(min, Math.min(max, val1));
    const normalizedValue1 = mapValueToPosition(boundedValue1, min, max, logExponent);
    const faderPosition1 = orientation === 'vertical' ? (1 - normalizedValue1) : normalizedValue1;

    const boundedValue2 = Math.max(min, Math.min(max, val2));
    const normalizedValue2 = mapValueToPosition(boundedValue2, min, max, logExponent);
    const faderPosition2 = orientation === 'vertical' ? (1 - normalizedValue2) : normalizedValue2;

    // State for dragging
    const [isDragging, setIsDragging] = useState(null); // 'fader1' or 'fader2'
    const faderRef = useRef(null);
    const startYRef = useRef(0);
    const startValRef = useRef(0);

    const handlePointerDown = (e) => {
        const target = e.target;
        if (target.classList.contains('fader-cap-1')) {
            setIsDragging('fader1');
            startValRef.current = boundedValue1;
        } else if (target.classList.contains('fader-cap-2')) {
            setIsDragging('fader2');
            startValRef.current = boundedValue2;
        } else {
            return; // Not a draggable element
        }

        if (orientation === 'vertical') {
            startYRef.current = e.clientY;
        } else {
            startYRef.current = e.clientX;
        }
        faderRef.current.setPointerCapture(e.pointerId);
    };

    const handlePointerMove = (e) => {
        if (!isDragging) return;
        
        let delta = 0;
        if (orientation === 'vertical') {
            delta = startYRef.current - e.clientY;
        } else {
            delta = e.clientX - startYRef.current;
        }

        const range = max - min;
        const deltaVal = (delta / (orientation === 'vertical' ? faderHeight : faderWidth)) * range;
        
        const newVal = clamp(startValRef.current + deltaVal, min, max);
        const roundedNewVal = Math.round(newVal * 100) / 100;

        if (isDragging === 'fader1') {
            onChange([roundedNewVal, val2]);
        } else if (isDragging === 'fader2') {
            onChange([val1, roundedNewVal]);
        }
    };

    const handlePointerUp = (e) => {
        setIsDragging(null);
        if (faderRef.current) {
            faderRef.current.releasePointerCapture(e.pointerId);
        }
    };

    const clamp = (val, min, max) => Math.max(min, Math.min(max, val));

    const faderStyles = {
        display: 'flex',
        flexDirection: orientation === 'vertical' ? 'column' : 'row',
        alignItems: 'center',
        width: orientation === 'vertical' ? faderWidth : faderHeight,
        height: orientation === 'vertical' ? faderHeight : faderWidth,
        position: 'relative',
        cursor: 'ns-resize', // default cursor
    };

    const trackStyles = {
        backgroundColor: trackColor,
        position: 'absolute',
        left: orientation === 'vertical' ? '50%' : '0%',
        top: orientation === 'vertical' ? '0%' : '50%',
        transform: orientation === 'vertical' ? 'translateX(-50%)' : 'translateY(-50%)',
        width: orientation === 'vertical' ? faderWidth * 0.4 : '100%',
        height: orientation === 'vertical' ? '100%' : faderWidth * 0.4,
        borderRadius: faderWidth * 0.2,
    };

    const capBaseStyles = {
        position: 'absolute',
        zIndex: 1,
        width: capWidth,
        height: capWidth,
        borderRadius: '50%',
        transition: 'background-color 0.1s ease',
    };

    const cap1Styles = {
        ...capBaseStyles,
        backgroundColor: capColor1,
        left: orientation === 'vertical' ? '50%' : undefined,
        top: orientation === 'vertical' ? undefined : '50%',
        transform: orientation === 'vertical'
            ? `translateX(-50%) translateY(${faderPosition1 * 100}%)`
            : `translateY(-50%) translateX(${faderPosition1 * 100}%)`,
    };

    const cap2Styles = {
        ...capBaseStyles,
        backgroundColor: capColor2,
        left: orientation === 'vertical' ? '50%' : undefined,
        top: orientation === 'vertical' ? undefined : '50%',
        transform: orientation === 'vertical'
            ? `translateX(-50%) translateY(${faderPosition2 * 100}%)`
            : `translateY(-50%) translateX(${faderPosition2 * 100}%)`,
    };

    // Adjust pointer based on orientation
    const pointerStyles = {
        backgroundColor: pointerColor,
        position: 'absolute',
        zIndex: 2,
        ...(orientation === 'vertical'
            ? {
                width: pointerWidth,
                height: pointerHeight,
                left: '50%',
                top: `${faderPosition1 * 100}%`, // Pointer typically linked to one fader, or middle? Let's assume first for now.
                transform: `translate(-50%, -50%)`,
                borderRadius: pointerWidth / 2,
            }
            : {
                width: pointerHeight,
                height: pointerWidth,
                top: '50%',
                left: `${faderPosition1 * 100}%`, // Pointer typically linked to one fader, or middle? Let's assume first for now.
                transform: `translate(-50%, -50%)`,
                borderRadius: pointerWidth / 2,
            }),
    };
    
    // Label styles
    const labelContainerStyles = {
        position: 'absolute',
        bottom: orientation === 'vertical' ? '0px' : undefined,
        left: orientation === 'vertical' ? undefined : '0px',
        right: orientation === 'vertical' ? '0px' : undefined,
        top: orientation === 'vertical' ? undefined : '0px',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        width: '100%',
        height: '100%',
        fontSize: '11px',
        color: '#aaa',
        fontWeight: 'bold',
        backgroundColor: 'rgba(0,0,0,0.5)',
        padding: '2px 6px',
        borderRadius: '3px',
        transform: orientation === 'vertical' ? 'rotate(-90deg)' : 'none',
        transformOrigin: orientation === 'vertical' ? 'center' : 'initial',
        whiteSpace: 'nowrap',
    };

    const title = config?.label?.En || config?.label_active?.En;

    return (
        <div
            ref={faderRef}
            style={faderStyles}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onPointerCancel={handlePointerUp}
        >
            <div style={trackStyles}></div>
            <div className="fader-cap-1" style={cap1Styles}></div>
            <div className="fader-cap-2" style={cap2Styles}></div>
            {/* Pointer usually follows one fader's position */}
            <div style={pointerStyles}></div>
            {title && <div style={labelContainerStyles}>{title}</div>}
        </div>
    );
};

window.DualFader = DualFader;