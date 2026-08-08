/**
 * Header: InputElements.jsx
 * Purpose: InputElements component or utility.
 * Description: Handles logic and rendering for InputElements component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// Inline comment: Logic for OcaCheckbox
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

// Inline comment: Logic for OcaIncDecButtons
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

// Inline comment: Logic for OcaDropdown
const OcaDropdown = ({ label, value, onChange, options = [], config }) => {
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

    // Resolve an option's label to a STRING (handles the label:{active,inactive}
    // schema, legacy label_active/label, or a plain string), localized.
    const resolveLabel = (o, key) => {
        const src = window.oaPickLabel ? window.oaPickLabel(o, 'active') : (o.label_active || o.label);
        if (src == null) return key !== undefined ? String(key) : '';
        if (typeof src === 'string') return src;
        return src[currentLang] || src.En || (key !== undefined ? String(key) : '');
    };

    // Normalize options to always be an array of { label (string), value }
    let normalizedOptions = [];
    if (Array.isArray(options)) {
        normalizedOptions = options.map(opt => typeof opt === 'string'
            ? { label: opt, value: opt }
            : { label: resolveLabel(opt, opt.value), value: opt.value });
    } else if (typeof options === 'object' && options !== null) {
        normalizedOptions = Object.entries(options).map(([key, opt]) => ({
            label: resolveLabel(opt, key),
            value: opt.value !== undefined ? opt.value : key,
        }));
    }
    // Ensure safeOptions is always an array, default to empty if normalization fails
    const safeOptions = Array.isArray(normalizedOptions) ? normalizedOptions : [];

    // Match the instrument's answer to an option — SHORT FORM INCLUDED.
    //
    // SCPI lets a mnemonic be written in full or truncated to its capitalised
    // head, and an instrument answers in the SHORT form: `:TRACe1:MODE WRITE`
    // is acknowledged as `WRIT`, MAXHOLD as `MAXH`, BLANK as `BLAN`. The option
    // values here are the long forms, so a literal comparison never matched and
    // <select> fell back to showing its first entry — the dropdown read LIVE
    // REALTIME for a trace that was actually in MIN HOLD.
    //
    // The short form is by definition a prefix of the long one, which is why a
    // prefix test is the right rule rather than a hand-kept alias table that
    // every new enum would have to be added to. Exact and case-insensitive
    // matches are tried first so a genuine option always wins over a prefix.
    const resolveValue = (v) => {
        if (v === undefined || v === null || v === '') return v;
        const s = String(v).trim();
        const exact = safeOptions.find(o => String(o.value) === s);
        if (exact) return exact.value;
        const ci = safeOptions.find(o => String(o.value).toUpperCase() === s.toUpperCase());
        if (ci) return ci.value;
        const short = safeOptions.filter(o => String(o.value).toUpperCase().startsWith(s.toUpperCase()));
        // Ambiguous prefix (two options sharing a head) is not a match — showing
        // the wrong one is worse than showing the raw reply.
        if (short.length === 1) return short[0].value;
        return v;
    };
    const selected = resolveValue(value);

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
            {label && <span style={{ fontSize: '12px', color: '#999', marginBottom: '4px' }}>{label}</span>}
            <select
                value={selected}
                onChange={(e) => onChange(e.target.value)}
                style={{
                    backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, '#222') : '#222'),
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