/**
 * Header: WinkButtonToggler.jsx
 * Purpose: WinkButtonToggler component or utility.
 * Description: Handles logic and rendering for WinkButtonToggler component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

/**
 * WinkButtonToggler — a radio/multi group of "wink" (shutter) buttons (mirror of
 * oaGuiElements/Core/buttons/button_wink_toggler, type `_WinkButtonToggler`).
 * Reuses OcaWinkButton for each option; the selected option is held OPEN (lit),
 * others closed. Selection semantics match ButtonToggler (radio default; multi
 * via `selection_mode`; `Allow_Null` lets a radio click clear).
 */
const WinkButtonToggler = ({ value, onChange, config, topic, nodeJson }) => {
    const useMqtt = !!topic;
    const useMqttState = window.useMqttState;
    const [lang] = window.useMqttLang ? window.useMqttLang() : ['En'];

    let opts = config?.options || {};
    if (Array.isArray(opts)) {
        const d = {}; opts.forEach((o) => { d[String(o)] = { label_active: { En: String(o) } }; }); opts = d;
    }
    const txt = (l, fb) => (!l ? fb : (typeof l === 'string' ? l : (l[lang] || l.En || fb)));

    let initial = "";
    const vDef = config?.value_default ?? config?.default_value;
    for (const [k, o] of Object.entries(opts)) {
        const yes = String(o?.selected ?? "").toLowerCase();
        if (yes === "yes" || yes === "true") { initial = k; break; }
        if (vDef != null && (k === String(vDef) || txt(window.oaPickLabel(o, 'active'), null) === String(vDef))) initial = k;
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

    const cols = parseInt(config?.layout_columns || config?.layout?.max_cols || config?.max_cols || 1, 10);
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
                        shape_type: config?.shape_type,
                        radius: config?.radius,
                        shutter_color: config?.shutter_color,
                        bezel_color: config?.bezel_color,
                        open_speed: config?.open_speed,
                        close_speed: config?.close_speed,
                        width: config?.width || 80,
                        height: config?.height || 30,
                        label_active: { En: txt(window.oaPickLabel(o, 'active'), key) },
                        label: undefined,
                    };
                    return (
                        <window.OcaWinkButton
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
window.WinkButtonToggler = WinkButtonToggler;
