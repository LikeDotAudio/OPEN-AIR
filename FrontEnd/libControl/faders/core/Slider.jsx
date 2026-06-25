// Slider Component (Track)
// Author: Gemini (Collaborator)
// Version: 20260505.1700.1
//
// Description: Renders the track element for the fader.

const Slider = ({ config, orientation, trackX, trackY, trackW, trackH }) => {
    const trackColor = config?.style?.track_color || '#333';
    const borderColor = '#222';
    const backgroundColor = '#050505';

    return (
        <rect x={trackX} y={trackY} width={trackW} height={trackH} fill={backgroundColor} stroke={borderColor} />
    );
};

window.FaderSlider = Slider;
