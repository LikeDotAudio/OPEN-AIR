/**
 * FaderDial: the "_Horizontal_with_dial_Value" composite — a horizontal fader
 * (whole-number part) + a rotary knob (decimal part) + a value readout. The two
 * controls add up to one number and operate independently.
 *
 * When given a % width it is FLUID: the fader bar fills the width, the knob is a
 * SQUARE sized to the height (always round), and value/label scale to height.
 * Everything redraws crisply (no zoom). Sizing is measured from the BORDER box
 * so it never feeds back into itself (no jiggle).
 */
const FaderDial = ({ value, onChange, config }) => {
    const title = config?.label?.En || config?.label_active?.En || "Composite";
    // min/max may live under domain.primary OR at the top level (the
    // _Horizontal_with_dial_Value schema stores them top-level, as strings).
    const _num = (v, d) => { const n = parseFloat(v); return Number.isNaN(n) ? d : n; };
    const min = _num(config?.domain?.primary?.min ?? config?.min ?? config?.value_min, 0);
    const max = _num(config?.domain?.primary?.max ?? config?.max ?? config?.value_max, 100);
    const units = config?.units || config?.unit_text || "";

    // Fader steps by step_coarse (whole); knob pitches by step_fine (decimal).
    // Readout shows decimals per `step` (its display resolution).
    const stepCoarse = parseFloat(config?.step_coarse) || 1;
    const stepFine = parseFloat(config?.step_fine ?? config?.step) || 0.001;
    const stepStr = String(config?.step ?? config?.step_fine ?? stepFine);
    const _dot = stepStr.indexOf('.');
    const decimals = _dot === -1 ? 0 : (stepStr.length - _dot - 1);
    const knobSteps = Math.max(1, Math.round(stepCoarse / stepFine)); // fine steps per coarse

    // Readout width is driven by the DOMAIN (max + precision), NOT the box height:
    // it must always fit the widest value the field can show, at full precision —
    // e.g. max 6000 at step .001 => "6000.000" (8 chars). Monospace => 1ch per
    // glyph, so the pixel width tracks the font size automatically.
    const fmtLen = (v) => (Number.isFinite(v) ? v.toFixed(decimals) : String(v ?? '')).length;
    const valueChars = Math.max(fmtLen(min), fmtLen(max), decimals + 2);

    const [inputValue, setInputValue] = React.useState((value !== undefined ? value : min).toFixed(decimals));
    React.useEffect(() => {
        setInputValue((value !== undefined ? value : min).toFixed(decimals));
    }, [value]);

    const handleTextChange = (e) => setInputValue(e.target.value);
    const handleTextBlur = () => {
        let parsed = parseFloat(inputValue);
        if (!isNaN(parsed)) {
            parsed = Math.max(min, Math.min(max, parsed));
            const rounded = Math.round(parsed / stepFine) * stepFine;
            onChange(rounded);
            setInputValue(rounded.toFixed(decimals));
        } else {
            setInputValue((value !== undefined ? value : min).toFixed(decimals));
        }
    };
    const handleTextKeyDown = (e) => { if (e.key === 'Enter') { handleTextBlur(); e.target.blur(); } };

    // Fluid when a % width is set; measure the border box (stable) for sizing.
    const fluid = typeof config?.layout?.width === 'string' && config.layout.width.trim().endsWith('%');
    const heightConstrained = config?.layout?.height != null;
    const rootRef = React.useRef(null);
    const [boxH, setBoxH] = React.useState(0);
    React.useEffect(() => {
        if (!fluid || !heightConstrained || !rootRef.current || typeof ResizeObserver === 'undefined') return;
        const ro = new ResizeObserver(() => {
            const h = rootRef.current ? rootRef.current.offsetHeight : 0;
            if (h > 0) setBoxH((p) => (p === h ? p : h));
        });
        ro.observe(rootRef.current);
        return () => ro.disconnect();
    }, [fluid, heightConstrained]);

    // Fluid-fill sizing: fader fills width, knob square to height (round).
    const H = (fluid && heightConstrained && boxH > 0) ? boxH : 80;
    const pad = Math.max(4, Math.min(12, Math.round(H * 0.12)));
    const labelFont = Math.max(8, Math.round(H * 0.20));
    const valueFont = Math.max(9, Math.round(H * 0.26));
    const knobSize = Math.max(16, H - pad * 2);
    const faderH = Math.max(14, H - pad * 2 - labelFont - 4); // leave room for the label above
    const gap = Math.max(6, Math.min(18, Math.round(H * 0.18)));

    // column_spacing [fader, knob, value] = left spacing of each sub-element.
    // Scales with the composite height when fluid; falls back to the uniform gap.
    const cs = Array.isArray(config?.column_spacing) ? config.column_spacing : null;
    const csScale = fluid ? (H / 80) : 1;
    const csM = (i) => cs ? `${Math.max(0, Math.round((cs[i] || 0) * csScale))}px` : undefined;

    const faderConfig = {
        ...config,
        ...config?.fader_config,
        fluid,
        // Give the embedded fader the resolved range (it reads domain.primary).
        domain: { primary: { min, max } },
        geometry: { ...config?.geometry, orientation: 'horizontal', width: fluid ? '100%' : 250, height: fluid ? faderH : 40 },
        show_value: false,
        show_label: false
    };

    const knobConfig = {
        ...config,
        ...config?.dial_config,
        geometry: { width: fluid ? knobSize : 60, height: fluid ? knobSize : 60 }, // square => always round
        style: { ...config?.style, knob_style: 'dial' },
        readout: { show_label: false, text_inside: false },
        domain: { primary: { min: 0, max: Math.max(1, knobSteps - 1) } }
    };

    // Decompose: fader = coarse part (multiples of step_coarse), knob = fine part
    // (step_fine increments). They add up and move independently.
    const value0 = (value !== undefined && value !== null) ? value : min;
    const coarse = Math.floor(value0 / stepCoarse) * stepCoarse;
    const fine = value0 - coarse;
    const knobVal = Math.max(0, Math.min(knobSteps - 1, Math.round(fine / stepFine)));
    const clampSnap = (nv) => {
        nv = Math.max(min, Math.min(max, nv));
        return Math.round(nv / stepFine) * stepFine;
    };
    const handleFaderChange = (v) => onChange(clampSnap(Math.round(v / stepCoarse) * stepCoarse + fine));
    const handleKnobChange = (k) => onChange(clampSnap(coarse + Math.max(0, Math.min(knobSteps - 1, k)) * stepFine));

    return (
        <div ref={rootRef} style={{
            display: 'flex', flexDirection: 'row', alignItems: 'center',
            backgroundColor: '#2b2b2b', padding: `${pad}px`, borderRadius: '4px',
            border: '1px solid #111', gap: cs ? 0 : `${gap}px`,
            width: fluid ? '100%' : 'fit-content',
            height: (fluid && heightConstrained) ? '100%' : 'auto',
            overflow: 'hidden', boxSizing: 'border-box',
        }}>
            {/* Left: Label & Fader (fills the width when fluid) */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: `${Math.round(gap / 3)}px`, marginLeft: csM(0), ...(fluid ? { flex: 1, minWidth: 0 } : {}) }}>
                <div style={{ fontSize: `${labelFont}px`, color: '#888', fontWeight: 'bold', textTransform: 'uppercase', paddingLeft: 5 }}>
                    {title}
                </div>
                {window.Fader && <window.Fader value={value0} onChange={handleFaderChange} config={faderConfig} />}
            </div>

            {/* Middle: Dial Knob (square => round) */}
            <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', flexShrink: 0, marginLeft: csM(1) }}>
                {window.Knob && <window.Knob value={knobVal} onChange={handleKnobChange} config={knobConfig} />}
            </div>

            {/* Right: Value & Units */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2, flexShrink: 0, marginLeft: csM(2) }}>
                <input type="text" value={inputValue}
                    onChange={handleTextChange} onBlur={handleTextBlur} onKeyDown={handleTextKeyDown}
                    style={{
                        width: `calc(${valueChars}ch + 4px)`, boxSizing: 'content-box',
                        backgroundColor: '#111', color: '#fff', border: '1px inset #222',
                        padding: '2px 4px', textAlign: 'center', fontFamily: 'monospace',
                        fontSize: `${valueFont}px`, borderRadius: '3px', outline: 'none',
                    }} />
                <div style={{ fontSize: `${labelFont}px`, color: '#888' }}>{units}</div>
            </div>
        </div>
    );
};

window.FaderDial = FaderDial;
