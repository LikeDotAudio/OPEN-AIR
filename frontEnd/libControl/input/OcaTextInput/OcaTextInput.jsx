// OcaTextInput Component
// Author: Gemini (Collaborator)
// Version: 20260507.1100.1
//
// Description: MQTT-synchronized text input field matching Python's BuilderTextValueWithUnitsCreator.

const OcaTextInput = ({ value, onChange, config, topic, nodeJson }) => {
    const useMqtt = !!topic;
    const useMqttState = window.useMqttState;
    const defaultVal = config?.value_default || "";
    const [val, setVal] = useMqtt ? useMqttState(topic, value !== undefined ? value : defaultVal, nodeJson) : [value !== undefined ? value : defaultVal, onChange, 'En'];
    const [lang] = window.useMqttLang ? window.useMqttLang() : ['En'];

    const getLocalizedText = (labelData, fallback) => {
        if (!labelData) return fallback;
        if (typeof labelData === 'string') return labelData;
        return labelData[lang] || labelData.En || fallback;
    };

    const label = getLocalizedText(config?.label_active || config?.label, "");

    const layout = config?.layout || {};
    const geom = config?.geometry || {};
    const fontSize = layout.font || geom.font || 13;
    const color = layout.colour || geom.colour || "#fff";

    const handleChange = (e) => {
        const next = e.target.value;
        if (useMqtt) setVal(next);
        else if (onChange) onChange(next);
    };

    return (
        <div style={{ display: 'flex', alignItems: 'center', width: '100%', padding: '5px 10px', height: '30px', boxSizing: 'border-box' }}>
            {label && (
                <div style={{ color: color, fontSize: `${fontSize}px`, fontWeight: 'bold', marginRight: '10px', whiteSpace: 'nowrap' }}>
                    {label}:
                </div>
            )}
            <input 
                type="text" 
                value={val} 
                onChange={handleChange}
                style={{
                    flexGrow: 1,
                    backgroundColor: '#1a1a1a',
                    color: color,
                    border: '1px solid #444',
                    borderRadius: '3px',
                    padding: '2px 8px',
                    fontSize: `${fontSize}px`,
                    outline: 'none',
                    fontFamily: 'Segoe UI, sans-serif'
                }}
            />
        </div>
    );
};

window.OcaTextInput = OcaTextInput;
