// OcaCheckbox Component
// Author: Gemini (Collaborator)
// Version: 20260507.1100.1
//
// Description: Canvas-like Checkbox with MQTT synchronization matching Python's BuilderCheckboxCreator.

const OcaCheckbox = ({ value, onChange, config, topic, nodeJson }) => {
    const useMqtt = !!topic;
    const useMqttState = window.useMqttState;
    const [val, setVal] = useMqtt ? useMqttState(topic, !!value, nodeJson) : [!!value, onChange, 'En'];
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
