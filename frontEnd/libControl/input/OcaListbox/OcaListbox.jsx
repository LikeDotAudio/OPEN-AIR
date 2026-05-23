// OcaListbox Component
// Author: Gemini (Collaborator)
// Version: 20260507.1200.1
//
// Description: Dynamic Listbox with MQTT synchronization matching Python's BuilderListboxCreator.
// Handles both Array and Object based options dictionaries.

const OcaListbox = ({ value, onChange, config, topic, nodeJson }) => {
    const useMqtt = !!topic;
    const useMqttState = window.useMqttState;
    const [val, setVal] = useMqtt ? useMqttState(topic, value || "", nodeJson) : [value || "", onChange, 'En'];
    const [lang] = window.useMqttLang ? window.useMqttLang() : ['En'];

    const getLocalizedText = (labelData, fallback) => {
        if (!labelData) return fallback;
        if (typeof labelData === 'string') return labelData;
        return labelData[lang] || labelData.En || fallback;
    };

    const label = getLocalizedText(config?.label_active || config?.label, "");
    
    // Parse options: normalize into an array of [key, config]
    let optionsData = config?.options || {};
    let normalizedOptions = [];

    if (Array.isArray(optionsData)) {
        normalizedOptions = optionsData.map(item => [String(item), { label: String(item), value: item }]);
    } else if (typeof optionsData === 'object') {
        normalizedOptions = Object.entries(optionsData).map(([key, opt]) => {
            // Handle simple string values in object: { "key": "label" }
            if (typeof opt === 'string') {
                return [key, { label: opt, value: key }];
            }
            return [key, opt];
        });
    }

    const sortedActiveOptions = normalizedOptions
        .filter(([_, opt]) => opt.active !== false)
        .sort((a, b) => (a[1].order || 0) - (b[1].order || 0));

    const handleSelect = (key, optValue) => {
        const nextVal = optValue !== undefined ? optValue : key;
        if (useMqtt) setVal(nextVal);
        else if (onChange) onChange(nextVal);
    };

    const colors = window.THEMES?.dark || { treeview_fg: "#dcdcdc", treeview_selected_bg: "#007acc", border: "#555" };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', width: '100%', minWidth: '150px', height: '150px', backgroundColor: '#1a1a1a', border: `1px solid ${colors.border}`, borderRadius: '4px', overflow: 'hidden' }}>
            {label && (
                <div style={{ fontSize: '10px', color: 'white', fontWeight: 'bold', padding: '5px 8px', borderBottom: '1px solid #333' }}>
                    {label.toUpperCase()}
                </div>
            )}
            <div style={{ flexGrow: 1, overflowY: 'auto', padding: '2px' }}>
                {sortedActiveOptions.map(([key, opt]) => {
                    const optLabel = getLocalizedText(opt.label_active || opt.label, key);
                    const optValue = opt.value !== undefined ? opt.value : key;
                    const isSelected = String(val) === String(optValue);

                    return (
                        <div 
                            key={key}
                            onClick={() => handleSelect(key, optValue)}
                            style={{
                                padding: '4px 8px',
                                fontSize: '12px',
                                color: isSelected ? '#fff' : colors.treeview_fg,
                                backgroundColor: isSelected ? colors.treeview_selected_bg : 'transparent',
                                cursor: 'pointer',
                                userSelect: 'none',
                                whiteSpace: 'nowrap',
                                transition: 'background-color: 0.1s'
                            }}
                            onMouseEnter={e => !isSelected && (e.currentTarget.style.backgroundColor = '#333')}
                            onMouseLeave={e => !isSelected && (e.currentTarget.style.backgroundColor = 'transparent')}
                        >
                            {optLabel}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

window.OcaListbox = OcaListbox;
