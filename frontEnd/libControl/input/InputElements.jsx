const OcaCheckbox = ({ label, checked, onChange }) => {
    return (
        <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', color: '#ccc' }}>
            <input 
                type="checkbox" 
                checked={checked} 
                onChange={(e) => onChange(e.target.checked)} 
                style={{
                    appearance: 'none',
                    backgroundColor: checked ? '#4caf50' : '#222',
                    border: '2px solid #555',
                    width: '20px',
                    height: '20px',
                    borderRadius: '4px',
                    marginRight: '10px',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center'
                }}
            />
            {label}
        </label>
    );
};

const OcaIncDecButtons = ({ label, value, onChange, step = 1, min = -100, max = 100 }) => {
    const inc = () => onChange(Math.min(max, value + step));
    const dec = () => onChange(Math.max(min, value - step));

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <span style={{ fontSize: '12px', color: '#999', marginBottom: '4px' }}>{label}</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <button onClick={dec} style={{ padding: '5px 10px', backgroundColor: '#444', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>-</button>
                <div style={{ backgroundColor: '#111', padding: '5px 10px', minWidth: '40px', textAlign: 'center', color: '#0f0', borderRadius: '4px', fontFamily: 'monospace' }}>
                    {value}
                </div>
                <button onClick={inc} style={{ padding: '5px 10px', backgroundColor: '#444', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>+</button>
            </div>
        </div>
    );
};

const OcaDropdown = ({ label, value, onChange, options = [] }) => {
    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '12px', color: '#999', marginBottom: '4px' }}>{label}</span>
            <select 
                value={value} 
                onChange={(e) => onChange(e.target.value)}
                style={{
                    backgroundColor: '#222',
                    color: '#fff',
                    border: '1px solid #555',
                    padding: '8px',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    outline: 'none'
                }}
            >
                {options.map((opt, i) => (
                    <option key={i} value={opt}>{opt}</option>
                ))}
            </select>
        </div>
    );
};

window.OcaCheckbox = OcaCheckbox;
window.OcaIncDecButtons = OcaIncDecButtons;
window.OcaDropdown = OcaDropdown;