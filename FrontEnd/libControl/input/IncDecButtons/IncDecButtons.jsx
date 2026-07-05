/**
 * Header: IncDecButtons.jsx
 * Purpose: IncDecButtons component or utility.
 * Description: Handles logic and rendering for IncDecButtons component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// IncDecButtons Component
// Author: Gemini (Collaborator)
// Version: 20260507.1000.1
//
// Description: Increment/Decrement buttons matching Python's BuilderInputIncDecButtonsCreator.

// Inline comment: Logic for IncDecButtons
const IncDecButtons = ({ value, onChange, config, topic, nodeJson }) => {
    const useMqtt = !!topic;
    const useMqttState = window.useMqttState;
    const defaultVal = config?.value_default || 0;
    const [val, setVal] = useMqtt ? useMqttState(topic, value !== undefined ? value : defaultVal, nodeJson) : [value !== undefined ? value : defaultVal, onChange, 'En'];
    const [lang] = window.useMqttLang ? window.useMqttLang() : ['En'];

    const incrementAmount = config?.increment || 1;

    const getLocalizedText = (labelData, fallback) => {
        if (!labelData) return fallback;
        if (typeof labelData === 'string') return labelData;
        return labelData[lang] || labelData.En || fallback;
    };

    const label = getLocalizedText(config?.label_active || config?.label, "");

    const handleInc = () => {
        const next = val + incrementAmount;
        if (useMqtt) setVal(next);
        else if (onChange) onChange(next);
    };

    const handleDec = () => {
        const next = val - incrementAmount;
        if (useMqtt) setVal(next);
        else if (onChange) onChange(next);
    };

    const btnStyle = {
        width: '30px',
        height: '30px',
        backgroundColor: '#333',
        color: '#fff',
        border: '1px solid #555',
        borderRadius: '4px',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        cursor: 'pointer',
        userSelect: 'none',
        fontSize: '14px'
    };

    return (
        <div style={{ display: 'flex', alignItems: 'center', backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, '#222') : '#222'), padding: '10px', borderRadius: '5px', border: '1px solid #444', gap: '10px' }}>
            {label && (
                <div style={{ fontSize: '12px', color: 'white', fontWeight: 'bold' }}>
                    {label}
                </div>
            )}
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <div 
                    style={btnStyle}
                    onPointerDown={(e) => { e.currentTarget.style.backgroundColor = '#555'; handleDec(); }}
                    onPointerUp={(e) => { e.currentTarget.style.backgroundColor = '#333'; }}
                    onPointerLeave={(e) => { e.currentTarget.style.backgroundColor = '#333'; }}
                >⬇</div>
                
                <div style={{ minWidth: '40px', textAlign: 'center', color: '#f4902c', fontFamily: 'monospace', fontSize: '14px', fontWeight: 'bold' }}>
                    {val}
                </div>

                <div 
                    style={btnStyle}
                    onPointerDown={(e) => { e.currentTarget.style.backgroundColor = '#555'; handleInc(); }}
                    onPointerUp={(e) => { e.currentTarget.style.backgroundColor = '#333'; }}
                    onPointerLeave={(e) => { e.currentTarget.style.backgroundColor = '#333'; }}
                >⬆</div>
            </div>
        </div>
    );
};

window.IncDecButtons = IncDecButtons;
