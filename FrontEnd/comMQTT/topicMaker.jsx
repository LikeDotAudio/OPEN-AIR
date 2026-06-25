// frontEnd/comMQTT/topicMaker.jsx
//
// Builds a HIERARCHICAL MQTT topic prefix from a Gui_Frames file path so the
// broker tree mirrors the on-disk folder hierarchy instead of a flat,
// underscore-joined leaf name:
//
//   /Window_1/left_50/top_100/0_Spectrum/10_YAK/1_N9340B/0_Frequency/yak_frequency.json
//     ->  "OpenAir/Gui/Spectrum/YAK/N9340B/Frequency"
//
// Each device folder becomes one topic level. The numeric ordering prefix
// (`0_`, `10_`) is stripped, and the window / screen-geometry container folders
// (Window_n, left/right/top/bottom/display) are dropped entirely — they describe
// where a frame sits on screen, not device identity, and were already absent
// from the legacy flat key (e.g. "Spectrum_YAK_N9340B_Frequency"). Trailing
// numbers on real device folders (e.g. "Channel_1") are PRESERVED.
//
// Loaded as a plain script (no JSX inside) so window.OaTopicMaker is defined
// before the Babel-compiled LoaderOrchestrator runs and asks for a prefix.
(function () {
    // Folders that describe windowing / screen geometry rather than the device
    // tree. A folder is skipped when its alphabetic base (with any leading
    // ordering prefix and trailing size suffix removed) matches one of these.
    const SKIP_TOKENS = new Set(['display', 'window', 'left', 'right', 'top', 'bottom']);
    const GUI_ROOT = 'OpenAir/Gui';

    // One folder name -> one cleaned topic level ('' means "drop this level").
    function normalizePart(rawPart) {
        if (!rawPart) return '';
        if (rawPart.toLowerCase() === 'oagui') return 'GUI';
        if (/^\d+$/.test(rawPart)) return '';                  // pure-numeric folder
        // Strip a leading "<n>_" / "<n>-" ordering prefix ("0_Spectrum" -> "Spectrum").
        const clean = rawPart.replace(/^\d+[_-]?/, '');
        // Drop window/geometry containers, recognised by their base token after
        // removing any trailing size suffix ("left_50" -> "left", "Window_1" -> "window").
        const base = clean.replace(/[_-]?\d+$/, '').toLowerCase();
        if (!clean || SKIP_TOKENS.has(base)) return '';
        return clean.replace(/\s+/g, '_');                     // spaces -> '_' within a level
    }

    // Folder path (trailing filename optional) -> "Spectrum/YAK/N9340B/Frequency".
    function segmentsFromFilePath(filePath) {
        if (!filePath || typeof filePath !== 'string') return '';
        let parts = filePath.split('/').filter(Boolean);
        if (parts.length && /\.[a-z0-9]+$/i.test(parts[parts.length - 1])) {
            parts = parts.slice(0, -1);                         // drop the file, keep its folders
        }
        return parts.map(normalizePart).filter(Boolean).join('/');
    }

    // Full GUI prefix: "OpenAir/Gui/Spectrum/YAK/N9340B/Frequency", or the bare
    // "OpenAir/Gui" root when no usable folder path is available.
    function buildGuiPrefix(filePath) {
        const segs = segmentsFromFilePath(filePath);
        return segs ? `${GUI_ROOT}/${segs}` : GUI_ROOT;
    }

    window.OaTopicMaker = { segmentsFromFilePath, buildGuiPrefix, GUI_ROOT, SKIP_TOKENS };
})();
