/**
 * Header: ButtonToggler.jsx
 * Purpose: ButtonToggler component or utility.
 * Description: Handles logic and rendering for ButtonToggler component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// ButtonToggler Component
// Author: Gemini (Collaborator)
// Version: 20260507.1000.1
//
// Description: Stateful radio group matching Python's TogglerButton.

// Inline comment: Logic for ButtonToggler
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

    // The topic carries the option's VALUE, never its key.
    //
    // The keys are ordering labels — "1".."7", plus "UNSELECTED" — while the
    // value is the quantity the instrument is being asked for. Publishing the
    // key sent `:SENSe:BANDwidth:RESolution 3` for the button whose value is
    // 0.1 MHz, which the N9340B accepted as 3 Hz, and `:…:RESolution UNSELECTED`
    // for the None button. Both are silent wrong answers: the panel lights the
    // button you pressed while the instrument is set to something else.
    //
    // Selection stays keyed INTERNALLY so rendering and multi-select are
    // unchanged; only what crosses the topic differs.
    const valueForKey = (key) => {
        const opt = optionsData[key];
        return (opt && opt.value !== undefined && opt.value !== null) ? String(opt.value) : String(key);
    };
    // Resolve what the INSTRUMENT said back to one of this control's keys.
    //
    // The panel and the instrument do not spell things the same way, and until
    // they are reconciled here a readback lights nothing at all:
    //
    //   count    the panel declares "50"; SCPI answers NR1 as "+50"
    //   on/off   the panel names ON and OFF; SCPI answers BOOL as 1 and 0
    //
    // Both were silent failures — the reading arrived, the widget could not
    // place it, and the control kept showing its authored default while the
    // instrument was somewhere else. Exact matches are tried first so a literal
    // option always wins over any of the looser rules.
    const keyForBusValue = (raw) => {
        const s = String(raw).trim();
        if (s === '') return null;
        const declared = Object.entries(optionsData)
            .filter(([, opt]) => opt && opt.value !== undefined && opt.value !== null);

        for (const [k, opt] of declared) {
            if (String(opt.value) === s) return k;
        }
        // Topics retained from before this change still hold a KEY. Resolve
        // those too, or every existing panel renders with nothing lit until the
        // control is touched once.
        if (Object.prototype.hasOwnProperty.call(optionsData, s)) return s;

        // NUMERIC equality, so "+50" finds "50". A leading plus, a trailing
        // ".0" and any zero padding are all the same quantity.
        const n = Number(s);
        if (Number.isFinite(n)) {
            for (const [k, opt] of declared) {
                if (Number(opt.value) === n) return k;
            }
            const numKey = Object.keys(optionsData).find(k => Number(k) === n);
            if (numKey !== undefined) return numKey;
        }

        // BOOL, spelled the instrument's way. Shares the truth table with YAK's
        // converter (as_bool) so a toggle cannot read as ON here while the SET
        // verb resolves the same payload as OFF.
        const b = { '1': true, 'true': true, 'on': true, 'yes': true,
                    '0': false, 'false': false, 'off': false, 'no': false }[s.toLowerCase()];
        if (b !== undefined) {
            const want = b ? 'ON' : 'OFF';
            const boolKey = Object.keys(optionsData).find(k => k.toUpperCase() === want);
            if (boolKey) return boolKey;
        }

        const ci = Object.keys(optionsData).find(k => k.toUpperCase() === s.toUpperCase());
        return ci !== undefined ? ci : null;
    };

    // "None Selected" is a rendered button whose value is the sentinel "NONE".
    // It means the control has no selection — it is not a quantity, and it must
    // never leave as one. Selecting it clears, exactly like deselecting does.
    const isNullKey = (key) =>
        key === 'UNSELECTED' ||
        String(optionsData[key] && optionsData[key].value).toUpperCase() === 'NONE';
    const nullKeys = Object.keys(optionsData).filter(isNullKey);

    // Find initial
    let initialSelectedKey = "";
    for (const [key, opt] of Object.entries(optionsData)) {
        if (String(opt?.selected || "no").toLowerCase() === "yes" || String(opt?.selected || "no").toLowerCase() === "true") {
            initialSelectedKey = key;
            break;
        }
    }

    const initialSelectedValue = initialSelectedKey ? valueForKey(initialSelectedKey) : "";
    const [val, setVal] = useMqtt ? useMqttState(topic, value !== undefined ? value : initialSelectedValue, nodeJson) : [value !== undefined ? value : initialSelectedValue, onChange, 'En'];
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

    // An empty topic value means "no selection", which is what the None button
    // renders as selected — the sentinel never travels, so it is reconstructed
    // here rather than read back off the bus.
    // ZERO IS A VALUE, not an absence. `val` was tested for truthiness, so the
    // instrument answering `0` for :INITiate:CONTinuous? or an averaging STATe?
    // fell into the no-selection branch and lit nothing — the one readback where
    // OFF is the whole answer. Only an empty/absent payload means "unset".
    const hasValue = val !== undefined && val !== null && String(val).trim() !== '';
    const currentSelectedKeys = hasValue
        ? String(val).split(",").map(keyForBusValue).filter(Boolean)
        : nullKeys;

    const handleOptionClick = (key) => {
        // Choosing "None Selected" is a clear, not a value to send.
        if (isNullKey(key)) {
            if (useMqtt) setVal(""); else if (onChange) onChange("");
            return;
        }

        let newKeys = [...currentSelectedKeys].filter(k => !isNullKey(k));

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

        const nextVal = newKeys.map(valueForKey).join(",");
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
        backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, '#222') : '#222'),
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
                    // label may be the new pair {active,inactive} or legacy flat keys.
                    const labelBase = getLocalizedText(window.oaPickLabel(opt, 'active'), key);
                    const onText = labelBase;
                    const offText = getLocalizedText(window.oaPickLabel(opt, 'inactive'), labelBase);
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
                                boxShadow: glow > 0 ? `inset 0 0 ${Math.min(40, glow * 3)}px ${currentBorder}` : (isSelected ? 'none' : 'inset 0 0 5px rgba(0,0,0,0.5)'),
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
