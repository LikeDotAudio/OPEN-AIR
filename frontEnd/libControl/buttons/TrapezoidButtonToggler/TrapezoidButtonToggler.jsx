/**
 * TrapezoidButtonToggler — a radio/multi group of trapezoid buttons (mirror of
 * oaGuiElements/Core/buttons/button_trapezoid_toggler, type
 * `_TrapezoidButtonToggler`). Reuses OcaTrapezoidButton for each option and the
 * same selection semantics as ButtonToggler (radio by default; `selection_mode`
 * "multi" enables multi-select; `Allow_Null` lets a radio click clear).
 */
const TrapezoidButtonToggler = ({ value, onChange, config, topic, nodeJson }) => {
    const useMqtt = !!topic;
    const useMqttState = window.useMqttState;
    const [lang] = window.useMqttLang ? window.useMqttLang() : ['En'];

    // options: array (["Mic","Line"]) or dict ({ "1": {label_active,color}, ... }).
    let opts = config?.options || {};
    if (Array.isArray(opts)) {
        const d = {}; opts.forEach((o) => { d[String(o)] = { label_active: { En: String(o) } }; }); opts = d;
    }

    const txt = (l, fb) => (!l ? fb : (typeof l === 'string' ? l : (l[lang] || l.En || fb)));

    // initial selection: option.selected, else value_default match.
    let initial = "";
    const vDef = config?.value_default ?? config?.default_value;
    for (const [k, o] of Object.entries(opts)) {
        const yes = String(o?.selected ?? "").toLowerCase();
        if (yes === "yes" || yes === "true") { initial = k; break; }
        if (vDef != null && (k === String(vDef) || txt(o.label_active, null) === String(vDef))) initial = k;
    }

    const [val, setVal] = useMqtt
        ? useMqttState(topic, value !== undefined ? value : initial, nodeJson)
        : [value !== undefined ? value : initial, onChange, 'En'];

    const smRaw = String(config?.selection_mode ?? "radio").toLowerCase();
    const mode = (smRaw === "multi" || smRaw === "many" || smRaw === "multiple") ? "multi" : "radio";
    const allowNull = config?.Allow_Null || false;
    const selected = val ? String(val).split(",") : [];

    const click = (key) => {
        let keys = [...selected];
        if (mode === "multi") keys = keys.includes(key) ? keys.filter((k) => k !== key) : [...keys, key];
        else keys = keys.includes(key) ? (allowNull ? [] : keys) : [key];
        const next = keys.join(",");
        useMqtt ? setVal(next) : (onChange && onChange(next));
    };

    const cols = parseInt(config?.layout?.max_cols || config?.layout_columns || config?.max_cols || Object.keys(opts).length || 1, 10);
    const groupLabel = txt(config?.label || config?.label_active, "");

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
            {groupLabel && <div style={{ fontSize: 10, color: '#ccc', fontWeight: 'bold' }}>{groupLabel}</div>}
            <div style={{ display: 'grid', gridTemplateColumns: `repeat(${cols}, auto)`, gap: 6 }}>
                {Object.entries(opts).map(([key, o]) => {
                    const isSel = selected.includes(key);
                    const btnCfg = {
                        ...config,
                        color: o.color || config?.color,
                        led_color: o.led_color || config?.led_color,
                        slant: config?.slant,
                        width: config?.width || 80,
                        height: config?.height || 50,
                        latching: true,
                        label_active: { En: txt(window.oaPickLabel(o, 'active'), key) },
                        label: undefined,
                    };
                    return (
                        <window.OcaTrapezoidButton
                            key={key}
                            label={txt(window.oaPickLabel(o, 'active'), key)}
                            value={isSel ? 1 : 0}
                            onChange={() => click(key)}
                            config={btnCfg}
                        />
                    );
                })}
            </div>
        </div>
    );
};
window.TrapezoidButtonToggler = TrapezoidButtonToggler;
