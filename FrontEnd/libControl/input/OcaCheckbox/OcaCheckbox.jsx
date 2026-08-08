/**
 * Header: OcaCheckbox.jsx
 * Purpose: OcaCheckbox component or utility.
 * Description: Handles logic and rendering for OcaCheckbox component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// OcaCheckbox Component
// Author: Gemini (Collaborator)
// Version: 20260507.1100.1
//
// Description: Canvas-like Checkbox with MQTT synchronization matching Python's BuilderCheckboxCreator.

// Inline comment: Logic for OcaCheckbox
const OcaCheckbox = ({ value, onChange, config, topic, nodeJson }) => {
    const useMqtt = !!topic;
    const useMqttState = window.useMqttState;
    const [rawVal, setVal] = useMqtt ? useMqttState(topic, !!value, nodeJson) : [!!value, onChange, 'En'];

    // An instrument answers a BOOL as 1 or 0, or as ON / OFF — never as a
    // JavaScript boolean. Two things go wrong if that is used as-is: the STRING
    // "0" is truthy, so an OFF marker rendered as ticked; and the NUMBER 0 makes
    // `{val && <svg/>}` evaluate to 0, which React renders as the literal
    // character "0" inside the box. Same truth table as YAK's as_bool, so a
    // checkbox cannot read as on while the SET verb resolves the same payload
    // as off.
    const asBool = (v) => {
        if (typeof v === 'boolean') return v;
        if (v === undefined || v === null) return false;
        const s = String(v).trim().toLowerCase();
        if (s === '') return false;
        if (['1', 'true', 'on', 'yes'].includes(s)) return true;
        if (['0', 'false', 'off', 'no'].includes(s)) return false;
        const n = Number(s);
        return Number.isFinite(n) ? n !== 0 : false;
    };
    const val = asBool(rawVal);
    const [lang] = window.useMqttLang ? window.useMqttLang() : ['En'];

    const getLocalizedText = (labelData, fallback) => {
        if (!labelData) return fallback;
        if (typeof labelData === 'string') return labelData;
        return labelData[lang] || labelData.En || fallback;
    };

    const onText = getLocalizedText(config?.label_active, getLocalizedText(config?.label, ""));
    const offText = getLocalizedText(config?.label_inactive, getLocalizedText(config?.label, ""));
    const labelText = val ? onText : offText;

    const handleToggle = () => {
        const next = !val;
        if (useMqtt) setVal(next);
        else if (onChange) onChange(next);
    };

    const boxSize = 16;

    return (
        <div 
            onClick={handleToggle}
            style={{ 
                display: 'flex', 
                alignItems: 'center', 
                padding: '5px 10px', 
                height: '30px', 
                cursor: 'pointer',
                userSelect: 'none'
            }}
        >
            <div style={{
                width: `${boxSize}px`,
                height: `${boxSize}px`,
                border: '1px solid white',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                marginRight: '10px',
                position: 'relative',
                backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, '#111') : '#111')
            }}>
                {val && (
                    <svg width={boxSize-4} height={boxSize-4} viewBox="0 0 10 10">
                        <path d="M1,5 L4,8 L9,2" fill="none" stroke="#00ff00" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                )}
            </div>
            <span style={{ color: 'white', fontSize: '12px', fontFamily: 'Segoe UI, sans-serif' }}>
                {labelText}
            </span>
        </div>
    );
};

window.OcaCheckbox = OcaCheckbox;
