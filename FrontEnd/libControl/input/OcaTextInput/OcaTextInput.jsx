/**
 * Header: OcaTextInput.jsx
 * Purpose: OcaTextInput component or utility.
 * Description: Handles logic and rendering for OcaTextInput component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// OcaTextInput Component
// Author: Gemini (Collaborator)
// Version: 20260507.1100.1
//
// Description: MQTT-synchronized text input field matching Python's BuilderTextValueWithUnitsCreator.

// Inline comment: Logic for OcaTextInput
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

    // A readout displays what an instrument answered; it must never publish to
    // the topic it is reading. `yak_readout` already points this widget at the
    // device's /Read topic, so an editable box there would let a keystroke
    // overwrite the instrument's reply.
    const readOnly = config?.read_only === true || config?.yak_readout === true;

    // One reply, several readouts.
    //
    // A device has exactly ONE `/Read` topic and the reply carries no
    // correlation, so four separate queries would overwrite each other and every
    // readout would show whichever answered last. The instrument already solves
    // this: `:FREQuency:STARt?;:FREQuency:STOP?;:FREQuency:CENTer?;:FREQuency:SPAN?`
    // returns all four in ONE round trip, semicolon-separated —
    //   +4.700000000E+08;+1.084000000E+09;+7.770000000E+08;+6.140000000E+08
    // `yak_readout_index` is how a widget claims its field of that reply.
    //
    // `yak_readout_scale` converts the instrument's units to the panel's (Hz to
    // MHz is 0.000001); `yak_readout_precision` fixes the decimals. Both are
    // optional — without them the field is shown exactly as it arrived, which is
    // the right default for anything non-numeric like *IDN?.
    const readoutIndex = config?.yak_readout_index;
    const displayVal = React.useMemo(() => {
        if (readoutIndex === undefined || readoutIndex === null) return val;
        const field = String(val === undefined || val === null ? '' : val).split(';')[readoutIndex];
        const raw = (field === undefined ? '' : String(field)).trim();
        if (raw === '') return '';
        const n = Number(raw);
        if (!Number.isFinite(n)) return raw;
        // Units first — the instrument's unit is declared, this widget's unit is
        // its own, and the conversion between them is arithmetic rather than a
        // hand-computed factor. `yak_readout_scale` remains as an escape hatch
        // for quantities the unit table does not model.
        const target = config?.units || (config?.domain && config.domain.units);
        let scaled;
        if (config?.yak_readout_unit && window.OaUnits) {
            scaled = window.OaUnits.convert(n, config.yak_readout_unit, target);
        } else {
            const scale = Number(config?.yak_readout_scale);
            if (!Number.isFinite(scale) || scale === 0) return raw;
            scaled = n * scale;
        }
        if (!Number.isFinite(Number(scaled))) return raw;
        const precision = Number(config?.yak_readout_precision);
        return Number.isFinite(precision) ? scaled.toFixed(precision) : String(scaled);
    }, [val, readoutIndex, config?.yak_readout_scale, config?.yak_readout_precision]);

    // COMMIT ON LEAVING THE CELL, not on every keystroke.
    //
    // Publishing per character sent the instrument every prefix of what was
    // being typed: entering 111 produced `:CALCulate:MARKer1:X 1000000`, then
    // 11 MHz, then 111 MHz — three commands, three readbacks, and two of them
    // moved the marker somewhere the operator never asked for. A text field is
    // not a fader; its value is not meaningful until it is finished.
    //
    // `draft` holds what is being typed; blur and Enter commit it, Escape
    // abandons it. While the field is untouched, `val` flows straight through,
    // so an instrument reading still updates the display.
    const [draft, setDraft] = React.useState(null);
    const shown = draft !== null ? draft : displayVal;

    const commit = () => {
        if (readOnly || draft === null) return;
        const next = draft;
        setDraft(null);
        if (useMqtt) setVal(next);
        else if (onChange) onChange(next);
    };

    const handleChange = (e) => {
        if (readOnly) return;
        setDraft(e.target.value);
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') { commit(); e.target.blur(); }
        else if (e.key === 'Escape') { setDraft(null); e.target.blur(); }
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
                value={shown}
                onChange={handleChange}
                onBlur={commit}
                onKeyDown={handleKeyDown}
                readOnly={readOnly}
                title={readOnly ? 'Reported by the instrument' : undefined}
                style={{
                    flexGrow: 1,
                    backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, '#1a1a1a') : '#1a1a1a'),
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
