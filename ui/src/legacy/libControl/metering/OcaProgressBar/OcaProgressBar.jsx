/**
 * Header: OcaProgressBar.jsx
 * Purpose: OcaProgressBar component or utility.
 * Description: Handles logic and rendering for OcaProgressBar component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

/**
 * OcaProgressBar Component
 */

// Inline comment: Logic for OcaProgressBar
const OcaProgressBar = ({ value, config }) => {
    const min = config?.min ?? 0;
    const max = config?.max ?? 100;
    const norm = Math.max(0, Math.min(1, (value - min) / (max - min || 1)));
    const color = config?.cosmetics?.colors?.primary || '#33A1FD';

    return (
        <div style={{ width: '100%', height: '10px', background: (window.OaTransparency ? window.OaTransparency.bg(config, '#222') : '#222'), borderRadius: '5px', overflow: 'hidden', border: '1px solid #444' }}>
            <div style={{ width: `${norm * 100}%`, height: '100%', background: color, transition: 'width 0.2s' }} />
        </div>
    );
};

window.OcaProgressBar = OcaProgressBar;
