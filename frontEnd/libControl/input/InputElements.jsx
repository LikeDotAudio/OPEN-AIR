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
                <div style={{ backgroundColor: '#111', padding: '5px 1p0px', minWidth: '40px', textAlign: 'center', color: '#0f0', borderRadius: '4px', fontFamily: 'monospace' }}>
                    {value}
                </div>
                <button onClick={inc} style={{ padding: '5px 10px', backgroundColor: '#444', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>+</button>
            </div>
        </div>
    );
};

const OcaDropdown = ({ label, value, onChange, options = [] }) => {
    let currentLang = 'En';
    let setLang = () => {};
    try {
        // Guard against hook calls during initial render or in non-component contexts
        if (window.useMqttLang) {
            [currentLang, setLang] = window.useMqttLang();
        }
    } catch (e) {
        console.warn("useMqttLang hook not available or called outside component:", e);
        // Fallback to default language if hook is not available
        currentLang = 'En'; 
    }

    // Normalize options to always be an array of { label, value }
    let normalizedOptions = [];
    if (Array.isArray(options)) {
        normalizedOptions = options.map(opt => typeof opt === 'string' ? { label: opt, value: opt } : opt);
    } else if (typeof options === 'object' && options !== null) {
        normalizedOptions = Object.entries(options).map(([key, opt]) => {
            const labelText = opt.label?.[currentLang] || opt.label?.En || key;
            return { label: labelText, value: key };
        });
    }
    // Ensure safeOptions is always an array, default to empty if normalization fails
    const safeOptions = Array.isArray(normalizedOptions) ? normalizedOptions : [];

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
            {label && <span style={{ fontSize: '12px', color: '#999', marginBottom: '4px' }}>{label}</span>}
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
                    outline: 'none',
                    minWidth: '100px'
                }}
            >
                {safeOptions.length > 0 ? safeOptions.map((opt, i) => (
                    <option key={i} value={opt.value}>{opt.label}</option>
                )) : <option value="">No Options</option>}
            </select>
        </div>
    );
};

window.OcaCheckbox = OcaCheckbox;
window.OcaIncDecButtons = OcaIncDecButtons;
window.OcaDropdown = OcaDropdown;