// Fader Component (OrchestrAator)
// Author: Gemini (Collaborator)
// Version: 20260505.1900.3
//
// Description: High-fidelity React Fader component using CSS classes for styling.

import React, { useState, useRef } from 'react';
import './Fader.css'; // Import the CSS file

// Ensure utility functions are available globally
const clamp = window.FaderUtils.clamp;
const mapValueToPosition = window.FaderUtils.mapValueToPosition; // Note: mapValueToPosition is not currently used in this render logic.

const Fader = ({ value: externalValue, onChange, config, topic, nodeJson }) => {
    // Domain configuration
    const min = config?.domain?.primary?.min !== undefined ? config.domain.primary.min : 0;
    const max = config?.domain?.primary?.max !== undefined ? config.domain.primary.max : 100;
    const logExponent = config?.domain?.primary?.log_exponent !== undefined ? config.domain.primary.log_exponent : 1.0;

    // MQTT integration
    const useMqtt = !!topic;
    const useMqttState = window.useMqttState;
    const [val, setVal] = useMqtt ? useMqttState(topic, externalValue || min, nodeJson) : [externalValue, onChange, 'En'];
    const currentValue = useMqtt ? val : (externalValue !== undefined ? externalValue : min);
    const setCurrentValue = useMqtt ? setVal : (val) => { if (onChange) onChange(val); };

    // Layout configuration
    const width = config?.geometry?.width || config?.layout?.width || 60;
    const height = config?.geometry?.height || config?.layout?.height || 250;
    
    // Orientation Inference
    const orientation = config?.style?.orientation || (width > height ? 'horizontal' : 'vertical');

    // Dimensions and scaling
    const trackSlotWidth = 10;
    const paddingStart = 25;
    const paddingEnd = 20;
    const totalLength = orientation === 'vertical' ? height : width;
    const range = max - min; // The fader range (value)
    const faderRange = totalLength - paddingStart - paddingEnd; // The fader range (pixels)

    const faderCapScale = config?.geometry?.fader_cap_scale || 1.0;
    const thumbSize = 40 * faderCapScale;

    const [isDragging, setIsDragging] = React.useState(false);
    const containerRef = React.useRef(null);

    // Interaction hook
    const { handlePointerDown, handlePointerMove, handlePointerUp } = window.useFaderInteraction(
        containerRef, orientation, min, max, faderRange, setCurrentValue, setIsDragging
    );

    // Calculate normalized position based on value, considering log scale
    const norm = (currentValue - min) / (max - min);
    const displayNorm = logExponent === 1.0 ? norm : Math.pow(Math.max(1e-7, norm), 1.0 / logExponent);
    const pos = clamp(displayNorm, 0, 1) * faderRange;

    // Calculate dimensions for track and thumb based on orientation and value
    const trackX = orientation === 'vertical' ? (width/2 - trackSlotWidth/2) : paddingStart;
    const trackY = orientation === 'vertical' ? paddingStart : (height/2 - trackSlotWidth/2);
    const trackW = orientation === 'vertical' ? trackSlotWidth : faderRange;
    const trackH = orientation === 'vertical' ? faderRange : trackSlotWidth;

    const thumbX = orientation === 'vertical' ? (width/2 - thumbSize/2) : (paddingStart + pos - thumbSize/2);
    const thumbY = orientation === 'vertical' ? (height - paddingEnd - pos - thumbSize/2) : (height/2 - thumbSize/2);

    // Dynamic styling classes for cap and track colors based on config
    // These classes will need corresponding definitions in Fader.css
    const capColorClass = config?.cosmetics?.colors?.cap ? 'cap-custom' : config?.cosmetics?.colors?.primary ? 'cap-primary' : '';
    const capHighlightClass = config?.cosmetics?.colors?.cap_highlights ? 'cap-highlight-custom' : '';
    const trackColorClass = config?.style?.track_color ? 'track-custom' : '';

    // Define CSS variable for dynamic positioning of the thumb
    const faderPosPx = orientation === 'vertical' ? thumbY : thumbX;

    return (
        <div ref={containerRef} className={`fader-container ${orientation}`} style={{ width, height, touchAction: 'none' }} onPointerDown={handlePointerDown} onPointerMove={handlePointerMove} onPointerUp={handlePointerUp}>
            {/* Track */}
            <div className={`fader-track ${orientation} ${trackColorClass}`} style={{ 
                width: trackW, 
                height: trackH,
                left: trackX,
                top: trackY
            }}></div>

            {/* Cap (Thumb) */}
            <div className={`fader-cap ${orientation} ${capColorClass} ${capHighlightClass}`} style={{ 
                '--fader-pos': faderPosPx, // CSS variable for dynamic positioning
                width: orientation === 'vertical' ? thumbSize : thumbSize / 1.5,
                height: orientation === 'vertical' ? thumbSize / 1.5 : thumbSize,
                left: orientation === 'vertical' ? `calc(50% - ${thumbSize/2}px)` : undefined,
                top: orientation === 'vertical' ? undefined : `calc(50% - ${orientation === 'vertical' ? thumbSize/1.5 : thumbSize}/2px)`,
                ...(orientation === 'vertical'
                    ? { transform: `translateX(-50%) translateY(calc(-1 * var(--fader-pos) + ${height - paddingEnd - thumbSize/2}px))` } // Vertical positioning adjustment
                    : { transform: `translateY(-50%) translateX(calc(var(--fader-pos) - ${paddingStart + thumbSize/2}px))` } // Horizontal positioning adjustment
                )
            }}>
                {/* Optional line inside the cap */}
                <div className="fader-cap-line"></div> 
            </div>
            {/* <window.FaderScale config={config} ... /> */}
        </div>
    );
};

window.Fader = Fader;