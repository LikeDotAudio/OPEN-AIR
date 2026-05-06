// Scale Component (Ticks and Labels)
// Author: Gemini (Collaborator)
// Version: 20260506.1400.2
//
// Description: Renders ticks and labels for the fader scale, 
// matching Python's ScaleDrawer logic, including custom ticks and colors.

const LABEL_THRESHOLDS = [[5000, 500], [1000, 200], [500, 50], [250, 20], [100, 10], [50, 5], [20, 2]];
const DRAWING_THRESHOLDS = [[500, 100], [200, 50], [50, 10], [20, 5], [10, 2], [5, 1]];

const Scale = ({ 
    min, max, logExponent, width, height, 
    availableLength, paddingStart, 
    tickSize, slotSize, capWidth,
    tickColor = 'lightgrey',
    subTickColor,
    tickTextColor,
    subTickTextColor,
    tickThickness = 1,
    tickLabelPosition = 'right',
    customTicks = null,
    orientation = 'vertical'
}) => {
    
    const effSubTickColor = subTickColor || tickColor;
    const effTickTextColor = tickTextColor || tickColor;
    const effSubTickTextColor = subTickTextColor || effSubTickColor;

    const calculateSmartInterval = (valRange) => {
        if (valRange <= 0) return 10.0;
        const rawInterval = valRange / 10.0;
        const exponent = Math.floor(Math.log10(rawInterval));
        const fractionalPart = rawInterval / Math.pow(10, exponent);

        let snapValue = 10;
        if (fractionalPart < 1.5) snapValue = 1;
        else if (fractionalPart < 3.5) snapValue = 2;
        else if (fractionalPart < 7.5) snapValue = 5;

        return snapValue * Math.pow(10, exponent);
    };

    const getTickValues = () => {
        if (customTicks && Array.isArray(customTicks)) {
            return customTicks;
        }
        const valRange = max - min;
        const tickInterval = calculateSmartInterval(valRange);
        const ticks = [];
        if (tickInterval > 0) {
            let current = Math.ceil(min / tickInterval) * tickInterval;
            while (current <= max) {
                ticks.push(current);
                current += tickInterval;
            }
        }
        return ticks;
    };

    const calculateTickIntervals = (numTicks) => {
        let labelInterval = 1;
        for (const [threshold, interval] of LABEL_THRESHOLDS) {
            if (numTicks > threshold) {
                labelInterval = interval;
                break;
            }
        }
        let drawInterval = 1;
        for (const [threshold, interval] of DRAWING_THRESHOLDS) {
            if (labelInterval >= threshold) {
                drawInterval = interval;
                break;
            }
        }
        return [labelInterval, drawInterval];
    };

    const calculateTextOffset = (containerDim, tickLengthHalf, capWidth, labelPos) => {
        let margin = 5;
        if (containerDim < 80) margin = 0;
        else if (containerDim < 100) margin = 2;

        return Math.max(tickLengthHalf, capWidth / 2) + margin;
    };

    const calculateTickPosition = (value) => {
        const range = max - min;
        const norm = (value - min) / range;
        const displayNorm = logExponent === 1.0 ? norm : Math.pow(Math.max(1e-7, norm), 1.0 / logExponent);
        
        if (orientation === 'vertical') {
            return availableLength * (1 - displayNorm) + paddingStart;
        } else {
            return availableLength * displayNorm + paddingStart;
        }
    };

    const tickValues = getTickValues();
    const [labelInterval, drawInterval] = calculateTickIntervals(tickValues.length);
    
    const containerDim = orientation === 'vertical' ? width : height;
    const tickLengthHalf = containerDim * tickSize;
    const labelOffset = calculateTextOffset(containerDim, tickLengthHalf, capWidth, tickLabelPosition);
    const center = containerDim / 2;
    const TICK_LINE_GAP = 2;

    // Sanitize label position for horizontal
    let labelPos = tickLabelPosition;
    if (orientation === 'horizontal' && (labelPos === 'left' || labelPos === 'right')) {
        labelPos = 'both';
    }

    return (
        <svg style={{ position: 'absolute', top: 0, left: 0, width, height, pointerEvents: 'none' }}>
            {tickValues.map((val, index) => {
                const pos = calculateTickPosition(val);
                const isMainTick = customTicks ? true : (index % labelInterval === 0);
                const shouldDraw = customTicks ? true : (index % drawInterval === 0);

                if (!shouldDraw) return null;

                const labelText = val === Math.floor(val) ? val.toString() : val.toFixed(1);
                const color = isMainTick ? tickColor : effSubTickColor;
                const textColor = isMainTick ? effTickTextColor : effSubTickTextColor;

                if (orientation === 'vertical') {
                    return (
                        <g key={index}>
                            {/* Left tick */}
                            <line 
                                x1={center - tickLengthHalf} y1={pos} 
                                x2={center - slotSize / 2 - TICK_LINE_GAP} y2={pos} 
                                stroke={color} strokeWidth={tickThickness} 
                            />
                            {/* Right tick */}
                            <line 
                                x1={center + slotSize / 2 + TICK_LINE_GAP} y1={pos} 
                                x2={center + tickLengthHalf} y2={pos} 
                                stroke={color} strokeWidth={tickThickness} 
                            />
                            {isMainTick && (
                                <>
                                    {(labelPos === 'right' || labelPos === 'both') && (
                                        <text 
                                            x={center + labelOffset} y={pos} 
                                            fill={textColor} fontSize="7" fontFamily="Arial" 
                                            alignmentBaseline="middle" textAnchor="start"
                                        >
                                            {labelText}
                                        </text>
                                    )}
                                    {(labelPos === 'left' || labelPos === 'both') && (
                                        <text 
                                            x={center - labelOffset} y={pos} 
                                            fill={textColor} fontSize="7" fontFamily="Arial" 
                                            alignmentBaseline="middle" textAnchor="end"
                                        >
                                            {labelText}
                                        </text>
                                    )}
                                </>
                            )}
                        </g>
                    );
                } else {
                    return (
                        <g key={index}>
                            {/* Top tick */}
                            <line 
                                x1={pos} y1={center - slotSize / 2 - TICK_LINE_GAP} 
                                x2={pos} y2={center - slotSize / 2 - TICK_LINE_GAP - tickLengthHalf} 
                                stroke={color} strokeWidth={tickThickness} 
                            />
                            {/* Bottom tick */}
                            <line 
                                x1={pos} y1={center + slotSize / 2 + TICK_LINE_GAP} 
                                x2={pos} y2={center + slotSize / 2 + TICK_LINE_GAP + tickLengthHalf} 
                                stroke={color} strokeWidth={tickThickness} 
                            />
                            {isMainTick && (
                                <>
                                    {(labelPos === 'top' || labelPos === 'both') && (
                                        <text 
                                            x={pos} y={center - labelOffset - slotSize/2 + 5} 
                                            fill={textColor} fontSize="7" fontFamily="Arial" 
                                            alignmentBaseline="baseline" textAnchor="middle"
                                        >
                                            {labelText}
                                        </text>
                                    )}
                                    {(labelPos === 'bottom' || labelPos === 'both') && (
                                        <text 
                                            x={pos} y={center + labelOffset + slotSize/2} 
                                            fill={textColor} fontSize="7" fontFamily="Arial" 
                                            alignmentBaseline="hanging" textAnchor="middle"
                                        >
                                            {labelText}
                                        </text>
                                    )}
                                </>
                            )}
                        </g>
                    );
                }
            })}
        </svg>
    );
};

window.FaderScale = Scale;