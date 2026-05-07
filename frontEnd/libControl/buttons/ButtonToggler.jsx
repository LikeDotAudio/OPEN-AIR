// ButtonToggler Component
// Author: Gemini (Collaborator)
// Version: 20260507.1000.1
//
// Description: Stateful radio group matching Python's TogglerButton.

const ButtonToggler = ({ value, onChange, config, topic, nodeJson }) => {
    const useMqtt = !!topic;
    const useMqttState = window.useMqttState;
    
    // Parse options
    let optionsData = config?.options || {};
    if (Array.isArray(optionsData)) {
        const optDict = {};
        optionsData.forEach(item => {
            optDict[String(item)] = { label: String(item) };
        });
        optionsData = optDict;
    }

    // Find initial
    let initialSelectedKey = "";
    for (const [key, opt] of Object.entries(optionsData)) {
        if (String(opt?.selected || "no").toLowerCase() === "yes" || String(opt?.selected || "no").toLowerCase() === "true") {
            initialSelectedKey = key;
            break;
        }
    }

    const [val, setVal] = useMqtt ? useMqttState(topic, value !== undefined ? value : initialSelectedKey, nodeJson) : [value !== undefined ? value : initialSelectedKey, onChange, 'En'];
    const [lang] = window.useMqttLang ? window.useMqttLang() : ['En'];

    const getLocalizedText = (labelData, fallback) => {
        if (!labelData) return fallback;
        if (typeof labelData === 'string') return labelData;
        return labelData[lang] || labelData.En || fallback;
    };

    const groupLabel = getLocalizedText(config?.label, "");

    const layout = config?.layout || {};
    const maxCols = parseInt(layout.max_cols || 4, 10);
    const gridPadX = parseInt(layout.padx || 5, 10);
    const gridPadY = parseInt(layout.pady || 5, 10);
    const selectionMode = (config?.selection_mode || "one").toLowerCase() === "one" ? "radio" : "multi";
    const allowNull = config?.Allow_Null || false;

    const currentSelectedKeys = val ? String(val).split(",") : [];

    const handleOptionClick = (key) => {
        let newKeys = [...currentSelectedKeys];
        
        if (selectionMode === "multi") {
            if (newKeys.includes(key)) {
                newKeys = newKeys.filter(k => k !== key);
            } else {
                newKeys.push(key);
            }
        } else {
            if (newKeys.includes(key)) {
                if (allowNull) newKeys = [];
            } else {
                newKeys = [key];
            }
        }

        const nextVal = newKeys.join(",");
        if (useMqtt) {
            setVal(nextVal);
        } else if (onChange) {
            onChange(nextVal);
        }
    };

    const containerStyle = {
        display: 'grid',
        gridTemplateColumns: `repeat(${maxCols}, 1fr)`,
        gap: `${gridPadY}px ${gridPadX}px`,
        backgroundColor: '#222',
        padding: '10px',
        borderRadius: '5px',
        border: '1px solid #444'
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
            {groupLabel && (
                <div style={{ fontSize: '10px', color: 'white', fontWeight: 'bold', marginBottom: '8px' }}>
                    {groupLabel}
                </div>
            )}
            <div style={containerStyle}>
                {Object.entries(optionsData).map(([key, opt]) => {
                    const labelBase = getLocalizedText(opt.label, key);
                    const onText = getLocalizedText(opt.label_active, labelBase);
                    const offText = getLocalizedText(opt.label_inactive, labelBase);
                    const valSuffix = opt.value || opt.units ? `\n(${opt.value || ''}${opt.units || ''})` : '';

                    const isSelected = currentSelectedKeys.includes(key);
                    const currentText = (isSelected ? onText : offText) + valSuffix;

                    const cAct = opt.active_color || config?.active_color || "#FF9900";
                    const cInact = opt.bg_color || config?.bg_color || "#1a1a1a";
                    const activeBgColor = config?.active_bg_color || "#000000";
                    const textColor = config?.text_color || "#888888";
                    const activeTextColor = config?.active_text_color || "#1a1a1a";
                    
                    const btnWidth = layout.width || 100;
                    const btnHeight = layout.height || 50;
                    const cornerRadius = layout.corner_radius || 6;

                    const currentBg = isSelected ? activeBgColor : cInact;
                    const currentBorder = isSelected ? cAct : '#555';
                    const currentTextColor = isSelected ? activeTextColor : textColor;

                    return (
                        <div 
                            key={key}
                            style={{
                                width: `${btnWidth}px`,
                                height: `${btnHeight}px`,
                                backgroundColor: currentBg,
                                border: `2px solid ${currentBorder}`,
                                borderRadius: `${cornerRadius}px`,
                                display: 'flex',
                                justifyContent: 'center',
                                alignItems: 'center',
                                cursor: 'pointer',
                                userSelect: 'none',
                                boxShadow: isSelected ? `0 0 8px ${cAct}60` : 'inset 0 0 5px rgba(0,0,0,0.5)',
                                transition: 'all 0.1s'
                            }}
                            onPointerDown={() => handleOptionClick(key)}
                        >
                            <span style={{ color: currentTextColor, fontSize: '11px', fontWeight: isSelected ? 'bold' : 'normal', textAlign: 'center', whiteSpace: 'pre-wrap', pointerEvents: 'none' }}>
                                {currentText}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

window.ButtonToggler = ButtonToggler;
