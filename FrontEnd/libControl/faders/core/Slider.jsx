/**
 * Header: Slider.jsx
 * Purpose: Slider component or utility.
 * Description: Handles logic and rendering for Slider component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// Slider Component (Track)
// Author: Gemini (Collaborator)
// Version: 20260505.1700.1
//
// Description: Renders the track element for the fader.

// Inline comment: Logic for Slider
const Slider = ({ config, orientation, trackX, trackY, trackW, trackH }) => {
    const trackColor = config?.style?.track_color || '#333';
    const borderColor = '#222';
    const backgroundColor = '#050505';

    return (
        <rect x={trackX} y={trackY} width={trackW} height={trackH} fill={backgroundColor} stroke={borderColor} />
    );
};

window.FaderSlider = Slider;
