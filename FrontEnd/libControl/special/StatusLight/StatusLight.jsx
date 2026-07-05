/**
 * Header: StatusLight.jsx
 * Purpose: StatusLight component or utility.
 * Description: Handles logic and rendering for StatusLight component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// Inline comment: Logic for StatusLight
const StatusLight = ({ value, config }) => {
    const title = config?.label_active?.En || config?.label?.En || "";
    const orientation = config?.Orientation || "horizontal";
    
    // Determine color based on MQTT value
    let fillColor = "#ff0000"; // Default Red
    if (value === "green" || value === true || value === 1 || value === "1" || value === "online") {
        fillColor = "#00ff00";
    } else if (value === "yellow" || value === "warning") {
        fillColor = "#ffff00";
    }

    const dotSize = 16;
    const style = {
        display: 'flex',
        flexDirection: orientation === 'vertical' ? 'column' : 'row',
        alignItems: 'center',
        gap: '10px',
        padding: '5px 10px',
        backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, '#1a1a1a') : '#1a1a1a'),
        borderRadius: '20px',
        border: '1px solid #333',
        width: 'fit-content'
    };

    return (
        <div style={style}>
            <div style={{
                width: dotSize,
                height: dotSize,
                borderRadius: '50%',
                backgroundColor: fillColor,
                boxShadow: `0 0 10px ${fillColor}, inset 0 0 5px rgba(0,0,0,0.5)`,
                border: '2px solid #fff'
            }} />
            {title && (
                <span style={{ color: '#fff', fontSize: '11px', fontWeight: 'bold', textTransform: 'uppercase' }}>
                    {title}
                </span>
            )}
        </div>
    );
};
window.StatusLight = StatusLight;