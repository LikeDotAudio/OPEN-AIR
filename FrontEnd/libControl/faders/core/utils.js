// Fader Utilities
// Author: Gemini (Collaborator)
// Version: 20260506.1100.1
//
// Description: Utility functions for fader components, matching Python geometry.

const clamp = (val, min, max) => Math.max(min, Math.min(max, val));

const mapValueToPosition = (value, min, max, logExponent) => {
    const range = max - min;
    if (range === 0) return 0;
    const norm = (value - min) / range;
    const displayNorm = logExponent === 1.0 ? norm : Math.pow(Math.max(1e-7, norm), 1.0 / logExponent);
    return clamp(displayNorm, 0, 1);
};

const mapPositionToValue = (pos, min, max, logExponent) => {
    const range = max - min;
    if (range === 0) return min;
    const norm = clamp(pos, 0, 1);
    const valueNorm = logExponent === 1.0 ? norm : Math.pow(norm, logExponent);
    return min + valueNorm * range;
};

window.FaderUtils = { clamp, mapValueToPosition, mapPositionToValue };
