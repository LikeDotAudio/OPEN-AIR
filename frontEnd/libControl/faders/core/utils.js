// Fader Utilities
// Author: Gemini (Collaborator)
// Version: 20260505.1700.1
//
// Description: Utility functions for fader components.

const clamp = (val, min, max) => Math.max(min, Math.min(max, val));

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

window.FaderUtils = { clamp, mapValueToPosition };
