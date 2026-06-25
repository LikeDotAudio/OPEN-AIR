const OcaButton = ({ label, onClick, color = '#444' }) => {
    return (
        <button 
            onClick={onClick}
            style={{
                padding: '10px 20px',
                backgroundColor: color,
                color: '#fff',
                border: '1px solid #222',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: 'bold',
                boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
                transition: 'all 0.1s'
            }}
            onMouseDown={e => {
                e.currentTarget.style.transform = 'translateY(2px)';
                e.currentTarget.style.boxShadow = '0 1px 2px rgba(0,0,0,0.3)';
            }}
            onMouseUp={e => {
                e.currentTarget.style.transform = 'none';
                e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.3)';
            }}
            onMouseLeave={e => {
                e.currentTarget.style.transform = 'none';
                e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.3)';
            }}
        >
            {label}
        </button>
    );
};

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