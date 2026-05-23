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
    // Canonical modes (sample.json legend): "radio" (one at a time) | "multi".
    // Only an explicit multi keyword enables multi-select; "radio"/"one"/unset
    // are single-select. (Old code only matched "one", so "radio" fell through
    // to multi — the bug where radio allowed multiple selections.)
    const smRaw = String(config?.selection_mode ?? "radio").toLowerCase();
    const selectionMode = (smRaw === "multi" || smRaw === "many" || smRaw === "multiple") ? "multi" : "radio";
    const allowNull = config?.Allow_Null || false;

    // Style schema: two parents `style.active` / `style.inactive`, each carrying
    // the SAME params (font_style, font_size, text_color, bg_color, border_color,
    // border_thickness, glow_intensity). Falls back to the LEGACY flat keys, which
    // historically lived under `style` (active_text_color, text_color, active_color,
    // active_bg_color, bg_color, glow_intensity, *_font_*) — reading them from
    // `config.style` here is what fixes active_text_color not rendering.
    const styleObj = config?.style || {};
    const A = styleObj.active || {};
    const I = styleObj.inactive || {};
    const pk = (...vals) => vals.find((v) => v !== undefined && v !== null);
    const grpActive = {
        text_color: pk(A.text_color, styleObj.active_text_color, '#1a1a1a'),
        bg_color: pk(A.bg_color, styleObj.active_bg_color, '#000000'),
        border_color: pk(A.border_color, styleObj.active_color, '#FF9900'),
        border_thickness: pk(A.border_thickness, 2),
        glow_intensity: pk(A.glow_intensity, styleObj.glow_intensity, 8),
        font_style: pk(A.font_style, styleObj.active_font_style, 'bold'),
        font_size: pk(A.font_size, styleObj.active_font_size),
    };
    const grpInactive = {
        text_color: pk(I.text_color, styleObj.text_color, '#888888'),
        bg_color: pk(I.bg_color, styleObj.bg_color, '#1a1a1a'),
        border_color: pk(I.border_color, '#555'),
        border_thickness: pk(I.border_thickness, 2),
        glow_intensity: pk(I.glow_intensity, 0),
        font_style: pk(I.font_style, styleObj.inactive_font_style, 'normal'),
        font_size: pk(I.font_size, styleObj.inactive_font_size),
    };

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

                    // Resolve the active/inactive style set for this state, with
                    // per-option color overrides (opt.active_color / opt.bg_color).
                    const s = isSelected ? grpActive : grpInactive;
                    const currentBg = isSelected ? grpActive.bg_color : (opt.bg_color || grpInactive.bg_color);
                    const currentBorder = isSelected ? (opt.active_color || grpActive.border_color) : grpInactive.border_color;
                    const currentTextColor = s.text_color;
                    const borderW = s.border_thickness || 2;
                    const fontWeight = s.font_style === 'bold' ? 'bold' : (s.font_style === 'italic' ? 'normal' : (s.font_style || 'normal'));
                    const fontStyleCss = s.font_style === 'italic' ? 'italic' : 'normal';
                    const fontSizeCss = s.font_size ? `${s.font_size}px` : '11px';
                    const glow = s.glow_intensity || 0;

                    // layout.width/height as a NUMBER = fixed per-button px (legacy).
                    // A %/string or unset => buttons fill their grid cell, so the
                    // toggler honors the element width set on its container.
                    const fixedBtnW = (typeof layout.width === 'number') ? layout.width : null;
                    const fixedBtnH = (typeof layout.height === 'number') ? layout.height : null;
                    const cornerRadius = layout.corner_radius || 6;

                    return (
                        <div
                            key={key}
                            style={{
                                width: fixedBtnW ? `${fixedBtnW}px` : '100%',
                                height: fixedBtnH ? `${fixedBtnH}px` : 50,
                                backgroundColor: currentBg,
                                border: `${borderW}px solid ${currentBorder}`,
                                borderRadius: `${cornerRadius}px`,
                                display: 'flex',
                                justifyContent: 'center',
                                alignItems: 'center',
                                cursor: 'pointer',
                                userSelect: 'none',
                                boxShadow: glow > 0 ? `0 0 ${Math.min(40, glow)}px ${currentBorder}99` : (isSelected ? 'none' : 'inset 0 0 5px rgba(0,0,0,0.5)'),
                                transition: 'all 0.1s'
                            }}
                            onPointerDown={() => handleOptionClick(key)}
                        >
                            <span style={{ color: currentTextColor, fontSize: fontSizeCss, fontWeight, fontStyle: fontStyleCss, textAlign: 'center', whiteSpace: 'pre-wrap', pointerEvents: 'none' }}>
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
