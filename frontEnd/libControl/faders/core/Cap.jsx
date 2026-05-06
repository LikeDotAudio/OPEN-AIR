// Cap Component (Thumb)
// Author: Gemini (Collaborator)
// Version: 20260505.1700.1
//
// Description: Renders the draggable cap/thumb of the fader.

const Cap = ({ config, orientation, thumbX, thumbY, thumbSize, pos }) => {
    const capColor = config?.knob_config?.cap_color || config?.cosmetics?.colors?.primary || '#33A1FD';
    const strokeColor = '#555';
    const line1Color = '#333';

    const capWidth = orientation === 'vertical' ? thumbSize : thumbSize / 1.5;
    const capHeight = orientation === 'vertical' ? thumbSize / 1.5 : thumbSize;

    return (
        <g transform={`translate(${thumbX}, ${thumbY})`}>
            <rect width={capWidth} height={capHeight} fill={capColor} rx="4" stroke={strokeColor} />
            <line x1={orientation === 'vertical' ? 10 : 15} y1={orientation === 'vertical' ? 15 : 10} 
                  x2={orientation === 'vertical' ? thumbSize - 10 : 25} y2={orientation === 'vertical' ? 15 : 30} stroke={line1Color} strokeWidth="2" />
        </g>
    );
};

window.FaderCap = Cap;
