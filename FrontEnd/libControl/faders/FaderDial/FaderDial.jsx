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
    const title = config?.label?.En || config?.label_active?.En || (typeof config?.label === 'string' ? config.label : "Composite");
    // show_label (hoisted from label.show_label by FieldComponent) toggles the
    // composite's title. Default: shown when the key is absent.
    const showLabel = config?.show_label !== false;
    // Container background is TRANSPARENT by default so the composite sits cleanly
    // on whatever panel/canvas is behind it (it's a control group, not a card).
    // OaTransparency still lets a node opt into a tint via cosmetics.bg_opacity, or
    // a solid fill via cosmetics.background. Border is dropped when transparent so
    // no orphan box outline remains.
    const _bgFill = config?.cosmetics?.background ?? config?.background ?? 'transparent';
    const rootBg = window.OaTransparency ? window.OaTransparency.bg(config, _bgFill) : _bgFill;
    const rootBorder = (rootBg && rootBg !== 'transparent') ? '1px solid #111' : 'none';
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

    // value may arrive as a string (e.g. "500" default) — coerce before toFixed.
    const safeNum = (v) => { const n = parseFloat(v); return Number.isFinite(n) ? n : min; };
    const [inputValue, setInputValue] = React.useState(safeNum(value).toFixed(decimals));
    React.useEffect(() => {
        setInputValue(safeNum(value).toFixed(decimals));
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
            setInputValue(safeNum(value).toFixed(decimals));
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
    // Cap auto-font at 24px so it doesn't get ridiculously large if H is massive (e.g. 140)
    const valueFont = Math.min(24, Math.max(9, Math.round(H * 0.26)));
    // Allow knob to scale up to 100 width as requested, but no larger
    const knobSize = Math.min(100, Math.max(16, H - pad * 2));
    const faderH = Math.max(14, H - pad * 2 - labelFont - 4); // fader uses full H so it stays tall!
    const gap = Math.max(6, Math.min(18, Math.round(H * 0.18)));

    // Value readout config (value_config.*): text colour, background, font px,
    // width in ch, height px. Falls back to the auto/scaled defaults.
    const vc = config?.value_config || {};
    const vColor = vc.colour || vc.color || '#fff';
    const vBgRaw = vc.bg_color || vc.background || '#111';
    const vBg = window.OaTransparency ? window.OaTransparency.bg(config, vBgRaw) : vBgRaw;
    const vFont = (vc.font != null) ? vc.font : (config?.layout?.font != null ? config.layout.font : valueFont);
    const vWidthCh = (vc.width != null) ? vc.width : valueChars;
    const vHeight = (vc.height != null) ? vc.height : null;

    // column_spacing [fader, knob, value] = the SHARE OF WIDTH each sub-element
    // column consumes. The three numbers are relative weights normalised to
    // percentages (so [122,30,10] => fader 75% / knob 19% / value 6%, and any
    // set that already sums to 100 maps 1:1). Each column's flex-basis is set to
    // its percentage; the uniform `gap` is dropped so the percentages add up to
    // the full row. Falls back to the auto layout (fader fills, knob/value to
    // content) when no column_spacing is present.
    const cs = Array.isArray(config?.layout?.column_spacing) ? config.layout.column_spacing
             : (Array.isArray(config?.column_spacing) ? config.column_spacing : null);
    const csTotal = cs ? cs.reduce((a, b) => a + (Math.max(0, parseFloat(b)) || 0), 0) : 0;
    const csPct = (i) => `${((Math.max(0, parseFloat(cs[i])) || 0) / csTotal) * 100}%`;
    // Per-column flex style: explicit % basis when column_spacing is set,
    // otherwise the supplied fallback (auto sizing).
    const colFlex = (i, fallback) =>
        (cs && csTotal > 0) ? { flex: `0 1 ${csPct(i)}`, minWidth: i === 0 ? 0 : 'min-content' } : fallback;

    const faderConfig = {
        ...config,
        ...config?.fader_config,
        fluid,
        // Give the embedded fader the resolved range (it reads domain.primary).
        domain: { primary: { min, max } },
        geometry: { ...config?.geometry, orientation: 'horizontal', width: fluid ? '100%' : 250, height: fluid ? faderH : 40 },
        show_value: false,
        show_label: false,
        // The composite renders its OWN title; never let the embedded fader draw a
        // duplicate label of its own.
        label: undefined,
        label_active: undefined
    };

    const knobConfig = {
        ...config,
        ...config?.dial_config,
        geometry: { width: fluid ? knobSize : 60, height: fluid ? knobSize : 60 }, // square => always round
        style: { ...config?.style, knob_style: 'dial' },
        readout: { show_label: false, text_inside: false },
        // The knob operates in INTEGER fine-step INDICES (0..knobSteps-1), not value
        // units — so its step/wheel must be index-based. Strip the parent's leaked
        // value-unit `step` (e.g. precision ".001", which would round the wheel to
        // "no change") and give it an index step big enough that one notch visibly
        // turns the dial.
        step: undefined,
        domain: { primary: { min: 0, max: Math.max(1, knobSteps - 1), step: Math.max(1, Math.round(knobSteps / 50)) } }
    };

    // Decompose: fader = coarse part (multiples of step_coarse), knob = fine part
    // (step_fine increments). They add up and move independently.
    const value0 = safeNum(value);
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
            backgroundColor: rootBg, padding: `${pad}px`, borderRadius: '4px',
            border: rootBorder, gap: cs ? 0 : `${gap}px`,
            width: fluid ? '100%' : 'fit-content',
            height: (fluid && heightConstrained) ? '100%' : 'auto',
            overflow: 'hidden', boxSizing: 'border-box',
        }}>
            {/* Left: Label & Fader (fills the width when fluid) */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: `${Math.round(gap / 3)}px`, ...colFlex(0, fluid ? { flex: 1, minWidth: 0 } : {}) }}>
                {showLabel && (
                    <div style={{ fontSize: `${config?.label_text_size ?? labelFont}px`, color: config?.label_text_color || '#888', fontWeight: 'bold', textTransform: 'uppercase', paddingLeft: 5 }}>
                        {title}
                    </div>
                )}
                {window.Fader && <window.Fader value={value0} onChange={handleFaderChange} config={faderConfig} />}
            </div>

            {/* Middle: Dial Knob (square => round) */}
            <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', ...colFlex(1, { flexShrink: 0 }) }}>
                {window.Knob && <window.Knob value={knobVal} onChange={handleKnobChange} config={knobConfig} />}
            </div>

            {/* Right: Value & Units */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2, ...colFlex(2, { flexShrink: 0 }) }}>
                <input type="text" value={inputValue}
                    onChange={handleTextChange} onBlur={handleTextBlur} onKeyDown={handleTextKeyDown}
                    style={{
                        width: `calc(${vWidthCh}ch + 4px)`, maxWidth: '100%', boxSizing: 'content-box',
                        ...(vHeight ? { height: `${vHeight}px` } : {}),
                        backgroundColor: vBg, color: vColor, border: '1px inset #222',
                        padding: '2px 4px', textAlign: 'center', fontFamily: 'monospace',
                        fontSize: `${vFont}px`, borderRadius: '3px', outline: 'none',
                    }} />
                <div style={{ fontSize: `${labelFont}px`, color: vColor }}>{units}</div>
            </div>
        </div>
    );
};

window.FaderDial = FaderDial;
