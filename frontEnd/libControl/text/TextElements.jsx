const OcaTextLabel = ({ label, fontSize = '14px', color = '#ccc', fontWeight = 'normal' }) => {
    return (
        <div style={{ fontSize, color, fontWeight, padding: '5px' }}>
            {label}
        </div>
    );
};

const OcaTextValueBox = ({ label, value, units = '' }) => {
    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <span style={{ fontSize: '12px', color: '#999', marginBottom: '4px' }}>{label}</span>
            <div style={{ 
                backgroundColor: '#111', 
                border: '1px inset #222', 
                padding: '5px 10px', 
                borderRadius: '4px',
                color: '#0f0',
                fontFamily: 'monospace',
                minWidth: '60px',
                textAlign: 'center'
            }}>
                {value} {units}
            </div>
        </div>
    );
};

window.OcaTextLabel = OcaTextLabel;
window.OcaTextValueBox = OcaTextValueBox;