/**
 * Header: OcaSliderValue.jsx
 * Purpose: OcaSliderValue component or utility.
 * Description: Handles logic and rendering for OcaSliderValue component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// OcaSliderValue Component
// Author: Gemini (Collaborator)
// Version: 20260507.1100.1
//
// Description: Composite Slider + Text Entry component matching Python's BuilderSliderValueCreator.

// Inline comment: Logic for OcaSliderValue
const OcaSliderValue = ({ value, onChange, config, topic, nodeJson }) => {
    const useMqtt = !!topic;
    const useMqttState = window.useMqttState;
    const [val, setVal] = useMqtt ? useMqttState(topic, value !== undefined ? value : (config?.value || 0), nodeJson) : [value !== undefined ? value : (config?.value || 0), onChange, 'En'];
    const [lang] = window.useMqttLang ? window.useMqttLang() : ['En'];

    const getLocalizedText = (labelData, fallback) => {
        if (!labelData) return fallback;
        if (typeof labelData === 'string') return labelData;
        return labelData[lang] || labelData.En || fallback;
    };

    const label = getLocalizedText(config?.label_active || config?.label, "");
    const units = config?.units || config?.unit_text || "";
    const min = parseFloat(config?.min || 0);
    const max = parseFloat(config?.max || 100);

    const handleSliderChange = (e) => {
        const next = parseFloat(e.target.value);
        if (useMqtt) setVal(next);
        else if (onChange) onChange(next);
    };

    const handleInputChange = (e) => {
        const next = parseFloat(e.target.value);
        if (!isNaN(next)) {
            const clamped = Math.max(min, Math.min(max, next));
            if (useMqtt) setVal(clamped);
            else if (onChange) onChange(clamped);
        }
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', width: '100%', padding: '10px', backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, '#222') : '#222'), borderRadius: '5px', border: '1px solid #444', boxSizing: 'border-box' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '12px', color: '#fff', fontWeight: 'bold' }}>{label}:</span>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                    <input 
                        type="number" 
                        value={val}
                        onChange={handleInputChange}
                        style={{
                            width: '60px',
                            backgroundColor: '#1a1a1a',
                            color: '#0f0',
                            border: '1px solid #444',
                            borderRadius: '3px',
                            textAlign: 'right',
                            fontSize: '12px',
                            marginRight: '5px',
                            outline: 'none'
                        }}
                    />
                    {units && <span style={{ fontSize: '10px', color: '#999' }}>{units}</span>}
                </div>
            </div>
            <input 
                type="range" 
                min={min} 
                max={max} 
                step={(max - min) / 100}
                value={val}
                onChange={handleSliderChange}
                style={{
                    width: '100%',
                    cursor: 'pointer',
                    accentColor: '#f4902c'
                }}
            />
        </div>
    );
};

window.OcaSliderValue = OcaSliderValue;
