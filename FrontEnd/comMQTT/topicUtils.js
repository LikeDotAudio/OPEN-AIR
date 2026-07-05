/**
 * Header: topicUtils.js
 * Purpose: topicUtils component or utility.
 * Description: Handles logic and rendering for topicUtils component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// frontEnd/comMQTT/topicUtils.js
//
// JS port of oaComProtocols/oaComMQTT/Methods/mqtt_topic_utils.py.
// Generates a hierarchical MQTT topic path from a JSON file's directory path,
// so web-published topics align with Python's MQTT tree
// (e.g. /Window_1/left_50/top_100/0_Spectrum/3_Instrument/1_frequency/frequency.json
//  -> "Window/Spectrum/Instrument/frequency").
(function () {
    const SKIP_TOKENS = new Set(['display', 'left', 'right', 'top', 'bottom']);

    function normalizePart(rawPart) {
        if (!rawPart) return '';
        if (rawPart.toLowerCase() === 'oagui') return 'GUI';
        if (SKIP_TOKENS.has(rawPart.toLowerCase())) return '';
        if (/^\d+$/.test(rawPart)) return '';
        let clean = rawPart.replace(/^(\d+)[_-]?/, '').replace(/[_-]?(\d+)$/, '');
        clean = clean.replace(/ /g, '_');
        if (!clean || SKIP_TOKENS.has(clean.toLowerCase())) return '';
        return clean;
    }

    window.generateTopicPathFromFilepath = function (filePath) {
        if (!filePath || typeof filePath !== 'string') return '';
        let parts = filePath.split('/').filter(Boolean);
        if (parts.length && /\.[a-z0-9]+$/i.test(parts[parts.length - 1])) {
            parts = parts.slice(0, -1);
        }
        return parts.map(normalizePart).filter(Boolean).join('/');
    };
})();
