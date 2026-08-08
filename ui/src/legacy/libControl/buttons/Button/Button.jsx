/**
 * Header: Button.jsx
 * Purpose: Button component or utility.
 * Description: Handles logic and rendering for Button component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// Inline comment: Logic for OcaButton
// `style` merges over the base look so consumers (e.g. the Sequencer toolbar)
// can compact/tint it while still inheriting any base style changes made here.
const OcaButton = ({ label, onClick, color = '#444', title, disabled, style }) => {
    const restShadow = (style && style.boxShadow) || '0 4px 6px rgba(0,0,0,0.3)';
    return (
        <button
            onClick={onClick}
            title={title}
            disabled={disabled}
            style={Object.assign({
                padding: '10px 20px',
                backgroundColor: color,
                color: '#fff',
                border: '1px solid #222',
                borderRadius: '4px',
                cursor: disabled ? 'default' : 'pointer',
                opacity: disabled ? 0.45 : 1,
                fontWeight: 'bold',
                boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
                transition: 'all 0.1s'
            }, style)}
            onMouseDown={e => {
                e.currentTarget.style.transform = 'translateY(2px)';
                e.currentTarget.style.boxShadow = '0 1px 2px rgba(0,0,0,0.3)';
            }}
            onMouseUp={e => {
                e.currentTarget.style.transform = 'none';
                e.currentTarget.style.boxShadow = restShadow;
            }}
            onMouseLeave={e => {
                e.currentTarget.style.transform = 'none';
                e.currentTarget.style.boxShadow = restShadow;
            }}
        >
            {label}
        </button>
    );
};

// Inline comment: Logic for OcaToggleButton
const OcaToggleButton = ({ label, value, onChange }) => {
    const isOn = value === 1 || value === true;
    
    return (
        <button 
            onClick={() => onChange(isOn ? 0 : 1)}
            style={{
                padding: '10px 20px',
                backgroundColor: isOn ? '#4caf50' : '#444',
                color: isOn ? '#fff' : '#ccc',
                border: '1px solid #222',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: 'bold',
                boxShadow: isOn ? 'inset 0 3px 5px rgba(0,0,0,0.5)' : '0 4px 6px rgba(0,0,0,0.3)',
                transition: 'all 0.2s'
            }}
        >
            {label}
        </button>
    );
};

window.OcaButton = OcaButton;
window.OcaToggleButton = OcaToggleButton;