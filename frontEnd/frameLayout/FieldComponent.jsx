// frameLayout/FieldComponent.jsx — the field/widget type dispatch + domain/value
// flatten. Translates a leaf node's `type` into the matching libControl widget.
window.FieldComponent = ({ nodeName, node: rawNode, path_prefix }) => {
    // Flatten the domain{} / value{} parents back onto the config so every widget
    // can read min/max/units/step*/default_value as before (migration-safe).
    // precision -> step (legacy readers); also expose domain.primary.
    const _d = (rawNode && rawNode.domain) || {};
    const _v = (rawNode && rawNode.value) || {};
    const _numU = (x) => { const n = parseFloat(x); return Number.isNaN(n) ? undefined : n; };
    const node = (rawNode && (rawNode.domain || rawNode.value)) ? {
        ...rawNode, ..._d, ..._v,
        step: _d.precision !== undefined ? _d.precision : rawNode.step,
        value_default: _v.default_value !== undefined ? _v.default_value
            : (_v.value_default !== undefined ? _v.value_default : rawNode.value_default),
        domain: {
            ..._d,
            primary: {
                ...(_d.primary || {}),
                ...(_d.min !== undefined ? { min: _numU(_d.min) } : {}),
                ...(_d.max !== undefined ? { max: _numU(_d.max) } : {}),
                ...(_v.default_value !== undefined ? { value_default: _numU(_v.default_value) } : {}),
            },
        },
    } : { ...rawNode };

    // Labels: new schema is label:{ active, inactive, (text) }. Expand back to
    // label_active/label_inactive so every widget that reads those keeps working
    // (migration-safe), without disturbing a plain `label` group title.
    const _lab = rawNode && rawNode.label;
    const _labIsPair = _lab && typeof _lab === 'object' && ('active' in _lab || 'inactive' in _lab);
    if (_labIsPair) {
        if (node.label_active === undefined) node.label_active = _lab.active;
        if (node.label_inactive === undefined) node.label_inactive = _lab.inactive !== undefined ? _lab.inactive : _lab.active;
    }

    const topic = `OpenAir/Gui${path_prefix}/${nodeName}`;

    // Determine default value
    let defaultVal = 0;
    if (node.domain?.primary?.value_default !== undefined) {
        defaultVal = node.domain.primary.value_default;
    } else if (node.value_default !== undefined) {
        defaultVal = node.value_default;
    }

    // Connect to MQTT global state store
    const useMqttStateHook = window.useMqttState || React.useState;
    const [val, setVal, lang] = useMqttStateHook(topic, defaultVal, node);
    
    const type = node.type || '';
    
    // ⚡ ROBUST LABEL RESOLUTION: Handle string or object-based localization
    const getLocalizedLabel = (labelData) => {
        if (!labelData) return null;
        if (typeof labelData === 'string') return labelData;
        return labelData[lang] || labelData.En || labelData.label?.[lang] || labelData.label?.En || null;
    };

    // Collapse a label:{active,inactive,text} pair to the LOCALIZED active STRING so
    // widgets that render config.label directly (e.g. LTPFader's {config.label})
    // never receive a raw object ("Objects are not valid as a React child").
    if (_labIsPair) {
        node.label = getLocalizedLabel(_lab.text) || getLocalizedLabel(_lab.active) || getLocalizedLabel(_lab.inactive) || '';
    }

    const title = getLocalizedLabel(node.label) ||
                  getLocalizedLabel(node.label_active) ||
                  nodeName;

    const lHeight = node.layout?.height || node.geometry?.height;
    const lWidth = node.layout?.width || node.geometry?.width;

    // A percentage width sizes the element as a % of its CONTAINER/panel (so
    // 100% fills the panel — it doesn't overflow the window). Responsive widgets
    // (fader, knob) then measure the resulting box and REDRAW to fit — a real
    // resize, not a zoom. alignItems:stretch lets the inner widget fill the box.
    const _pctFrac = (v) => (typeof v === 'string' && v.trim().endsWith('%')) ? (parseFloat(v) / 100) : null;
    const pw = _pctFrac(node.layout?.width);
    const ph = _pctFrac(node.layout?.height);
    const scaling = pw != null || ph != null;

    const style = {
        display: 'flex',
        flexDirection: 'column',
        alignItems: scaling ? 'stretch' : 'center',
        margin: scaling ? 0 : '0 auto',
        width: pw != null ? `${pw * 100}%` : (lWidth != null ? window.oaCssLen(lWidth) : '100%'),
        // Honor an explicit height (px or %); otherwise auto when scaling so the
        // widget sizes to content.
        height: lHeight != null ? (ph != null ? `${ph * 100}%` : window.oaCssLen(lHeight)) : (scaling ? 'auto' : '100%'),
        boxSizing: 'border-box',
    };

    // When a field is %-sized, mark its widget fluid so responsive widgets
    // (fader, knob) measure their box and redraw to fit (crisp).
    const fluidConfig = scaling ? { ...node, fluid: true } : node;
    const titleStyle = { fontSize: '12px', color: node.cosmetics?.colors?.text || '#999', marginBottom: '10px' };

    // _Horizontal_with_dial_Value is the canonical composite. _CompositeFader /
    // _GCA / GCA are deprecated styles that now render as this one too.
    if (type.toLowerCase().includes('composite') || type.toLowerCase().includes('dial_value') || type === '_Horizontal_with_dial_Value' || type === '_GCA' || type === 'GCA') {
        return (
            <div style={style}>
                {window.FaderDial ? <window.FaderDial value={val} onChange={setVal} config={node} /> : <div style={{width: '200px', height: '60px', background: '#333'}}></div>}
            </div>
        );
    }

    if (type.toLowerCase().includes('dual')) {
        return (
            <div style={style}>
                <span style={titleStyle}>{title}</span>
                {window.DualFader ? <window.DualFader value={val} onChange={setVal} config={node} /> : <div style={{width: '60px', height: '150px', background: '#333'}}></div>}
            </div>
        );
    }

    if (type.toLowerCase().includes('ltp')) {
        return (
            <div style={style}>
                <span style={titleStyle}>{title}</span>
                {window.LTPFader ? <window.LTPFader value={val} onChange={setVal} config={node} /> : <div style={{width: '60px', height: '150px', background: '#444', borderRadius: '30px'}}></div>}
            </div>
        );
    }

    if (type === '_SmartFader' || type.toLowerCase().includes('fader')) {
        if (type === '_FaderWithBarGraph') {
            return (
                <div style={style}>
                    {window.FaderWithMeter ? <window.FaderWithMeter value={val} onChange={setVal} config={node} /> : <div style={{width: '100px', height: '150px', background: '#444'}}></div>}
                </div>
            );
        }
        return (
            <div style={style}>
                <span style={titleStyle}>{title}</span>
                {window.Fader ? <window.Fader value={val} onChange={setVal} config={fluidConfig} /> : <div style={{width: '30px', height: '150px', background: '#444'}}></div>}
            </div>
        );
    }

    if (type === '_VUMeterKnob' || type === '_Meter_Knob_With_Vu_Meter' || (type.toLowerCase().includes('knob') && type.toLowerCase().includes('vu'))) {
        return (
            <div style={style}>
                {window.VUMeterKnob ? <window.VUMeterKnob value={val} onChange={setVal} config={node} topic={topic} path_prefix={path_prefix} /> : <div style={{width: '150px', height: '150px', background: '#333'}}>VU Knob</div>}
            </div>
        );
    }

    if (type.toLowerCase().includes('meter') || type === '_BarGraph' || type === '_SmartMeter' || type === '_Meter' || type === 'DynamicBarGraph' || type.toLowerCase().includes('bargraph')) {
        if (type.toLowerCase().includes('needle')) {
            return (
                <div style={style}>
                    {window.NeedleMeter ? <window.NeedleMeter value={val} config={node} /> : <div style={{width: '100px', height: '100px', background: 'darkred', borderRadius: '50% 50% 0 0'}}></div>}
                </div>
            );
        }
        return (
            <div style={style}>
                <span style={titleStyle}>{title}</span>
                {window.MeterBarGraph ? <window.MeterBarGraph value={val} config={node} /> : <div style={{width: '20px', height: '150px', background: 'green'}}></div>}
            </div>
        );
    }

    if (type.toLowerCase().includes('cmdp') || type.toLowerCase().includes('mdp') || type.toLowerCase().includes('knob') || type === 'SelectorSwitch') {
        let Widget = window.Knob;
        if (type === 'SelectorSwitch') Widget = window.SelectorSwitch;
        else if (type.toLowerCase().includes('cmdp')) Widget = window.CMDP || window.Knob;
        else if (type.toLowerCase().includes('mdp')) Widget = window.MDP || window.Knob;
        
        return (
            <div style={style}>
                <span style={titleStyle}>{title}</span>
                {Widget ? <Widget value={val} onChange={setVal} config={fluidConfig} size={100}/> : <div style={{width: '100px', height: '100px', borderRadius:'50%', background: '#444'}}></div>}
            </div>
        );
    }

    if (type === '_DataJsonTree' || type.toLowerCase().includes('json')) {
        return (
            <div style={{ ...style, height: node?.layout?.height || '400px' }}>
                {window.OcaJsonTree ? <window.OcaJsonTree value={val} config={node} /> : <div style={{background: '#222', color: '#fff'}}>JSON Tree</div>}
            </div>
        );
    }

    if (type.toLowerCase().includes('keyboard') || type.toLowerCase().includes('midi')) {
        return (
            <div style={style}>
                {window.MidiKeyboard ? <window.MidiKeyboard value={val} onChange={setVal} config={node} /> : <div style={{background: '#222', color: '#fff'}}>MIDI Keyboard</div>}
            </div>
        );
    }

    if (type.toLowerCase().includes('progress') || type === 'ProgressBar' || type === '_ProgressBar' || type === '_SmartProgress') {
        return (
            <div style={style}>
                {window.OcaProgressBar ? <window.OcaProgressBar value={val} config={node} topic={topic} nodeJson={node} /> : <div style={{width: '100%', height: '20px', background: '#333'}}>Progress</div>}
            </div>
        );
    }

    if (type.toLowerCase().includes('status_light') || type.toLowerCase().includes('indicator') || type === '_SmartLight') {
        return (
            <div style={style}>
                {window.StatusLight ? <window.StatusLight value={val} config={node} /> : <div style={{width: '15px', height: '15px', borderRadius: '50%', background: 'red'}}></div>}
            </div>
        );
    }

    if (type === 'AnimationDisplay' || type.toLowerCase().includes('animation')) {
        return (
            <div style={style}>
                {window.AnimationDisplay ? <window.AnimationDisplay value={val} config={node} /> : <div style={{background: '#222', color: '#fff'}}>Animation</div>}
            </div>
        );
    }

    if (type.toLowerCase().includes('image_display') || type.toLowerCase().includes('picture') || type === '_GuiImage' || type.toLowerCase().includes('image')) {
        return (
            <div style={style}>
                {window.ImageDisplay ? <window.ImageDisplay value={val} config={node} /> : <div style={{background: '#222', color: '#fff'}}>Image</div>}
            </div>
        );
    }

    if (type.toLowerCase().includes('break_line') || type.toLowerCase().includes('breakline') || type.toLowerCase().includes('separator')) {
        return (
            <div style={style}>
                {window.BreakLine ? <window.BreakLine config={node} /> : <hr />}
            </div>
        );
    }

    if (type === '_Radar' || type.toLowerCase().includes('radar')) {
        return (
            <div style={style}>
                {window.Radar ? <window.Radar value={val} config={node} /> : <div style={{width: '200px', height: '200px', borderRadius: '50%', background: '#111'}}>Radar</div>}
            </div>
        );
    }

    if (type === 'DynamicGraph' || type === 'plot_widget' || type.toLowerCase().includes('graph')) {
        return (
            <div style={style}>
                {window.DynamicGraph ? <window.DynamicGraph value={val} config={node} topic={topic} nodeJson={node} /> : <div style={{width: '100%', height: '300px', background: '#222'}}>Graph Component</div>}
            </div>
        );
    }

    if (type === '_SmartNav' || type.toLowerCase().includes('directional')) {
        return (
            <div style={style}>
                {window.DirectionalButtons ? <window.DirectionalButtons config={node} topic={topic} nodeJson={node} /> : <div style={{background: '#333'}}>Dir Buttons</div>}
            </div>
        );
    }

    if (type === '_SmartIncDec' || type.toLowerCase().includes('inc_dec') || type.toLowerCase().includes('incdec')) {
        return (
            <div style={style}>
                {window.IncDecButtons ? <window.IncDecButtons value={val} onChange={setVal} config={node} topic={topic} nodeJson={node} /> : <div style={{background: '#333'}}>IncDec Buttons</div>}
            </div>
        );
    }

    if (type === 'OcaTable' || type.toLowerCase().includes('table')) {
        return (
            <div style={style}>
                {window.OcaTable ? <window.OcaTable value={val} config={node} /> : <div style={{background: '#222', color: '#fff'}}>Table</div>}
            </div>
        );
    }

    if (type.toLowerCase().includes('button') || type.toLowerCase().includes('actuator') || type.toLowerCase().includes('toggle')) {
        const isWink = type.toLowerCase().includes('wink');
        const isTrapezoid = type.toLowerCase().includes('trapezoid');
        const isTogglerGroup = type.toLowerCase().includes('toggler') || (node.options && typeof node.options === 'object' && Object.keys(node.options).length > 1 && !isWink && !isTrapezoid);
        const isDirectional = type.toLowerCase().includes('directional');
        const isIncDec = type.toLowerCase().includes('inc_dec') || type.toLowerCase().includes('incdec');

        if (isDirectional) {
            return (
                <div style={style}>
                    {window.DirectionalButtons ? <window.DirectionalButtons config={node} topic={topic} nodeJson={node} /> : <div style={{background: '#333'}}>Dir Buttons</div>}
                </div>
            );
        }

        if (isIncDec) {
            return (
                <div style={style}>
                    {window.IncDecButtons ? <window.IncDecButtons value={val} onChange={setVal} config={node} topic={topic} nodeJson={node} /> : <div style={{background: '#333'}}>IncDec Buttons</div>}
                </div>
            );
        }

        if (isTogglerGroup) {
            // For a toggler, layout.width/height are the PER-BUTTON dimensions
            // (consumed inside ButtonToggler), not the container size. Force the
            // container full-width so alignItems:center can center the button grid
            // in the block cell (instead of pinning it left), and height:auto so a
            // multi-row grid grows down naturally instead of overflowing a 50px box
            // and overlapping the next block.
            // Shape variants: trapezoid / wink toggler GROUPS get their own
            // components (each renders the matching single-button shape per option,
            // sharing the radio/multi selection semantics). Fallback: rect toggler.
            const TogglerComp = (isTrapezoid && window.TrapezoidButtonToggler) ? window.TrapezoidButtonToggler
                : (isWink && window.WinkButtonToggler) ? window.WinkButtonToggler
                : window.ButtonToggler;
            return (
                <div style={{ ...style, width: pw != null ? `${pw * 100}%` : '100%', height: 'auto' }}>
                    {TogglerComp ? <TogglerComp value={val} onChange={setVal} config={node} topic={topic} nodeJson={node} /> : <div style={{background: '#333'}}>Button Toggler</div>}
                </div>
            );
        }

        // Single buttons
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '10px' }}>
                {isWink ? (
                    window.OcaWinkButton ? <window.OcaWinkButton label={title} value={val} onChange={setVal} config={node} topic={topic} /> : <button>{title}</button>
                ) : isTrapezoid ? (
                    window.OcaTrapezoidButton ? <window.OcaTrapezoidButton label={title} value={val} onChange={setVal} config={node} topic={topic} /> : <button>{title}</button>
                ) : (
                    window.ButtonToggle ? <window.ButtonToggle value={val} onChange={setVal} config={node} topic={topic} nodeJson={node} /> : <button>{title}</button>
                )}
            </div>
        );
    }

    if (type.toLowerCase().includes('checkbox') || type === '_Checkbox') {
        return (
            <div style={style}>
                {window.OcaCheckbox ? <window.OcaCheckbox value={val} onChange={setVal} config={node} topic={topic} nodeJson={node} /> : <input type="checkbox" />}
            </div>
        );
    }

    // Dropdown = a native <select> menu (OcaDropdown), distinct from the scrolling
    // OcaListbox. `_GuiDropDownOption` and any 'dropdown' type render as a menu.
    if (type === '_GuiDropDownOption' || type.toLowerCase().includes('dropdown')) {
        return (
            <div style={style}>
                {window.OcaDropdown
                    ? <window.OcaDropdown label={title} value={val} onChange={setVal} options={node.options} />
                    : <select><option>{title}</option></select>}
            </div>
        );
    }

    if (type.toLowerCase().includes('listbox') || type === '_Listbox' || type === '_SmartList') {
        return (
            <div style={style}>
                {window.OcaListbox ? <window.OcaListbox value={val} onChange={setVal} config={node} topic={topic} nodeJson={node} /> : <select><option>{title}</option></select>}
            </div>
        );
    }

    if (type.toLowerCase().includes('label') || type.startsWith('_Label') || type === '_GuiLabel') {
        return (
            <div style={style}>
                {window.OcaTextLabel ? <window.OcaTextLabel value={val} config={node} /> : <span>{title}</span>}
            </div>
        );
    }

    if (type.toLowerCase().includes('value') || type === '_TextInput' || type === '_SliderValue' || type === '_SmartInput') {
        if (type === '_SliderValue' || type.toLowerCase().includes('slider')) {
            return (
                <div style={style}>
                    {window.OcaSliderValue ? <window.OcaSliderValue value={val} onChange={setVal} config={node} topic={topic} nodeJson={node} /> : <span>{val}</span>}
                </div>
            );
        }
        return (
            <div style={style}>
                {window.OcaTextInput ? <window.OcaTextInput value={val} onChange={setVal} config={node} topic={topic} nodeJson={node} /> : (
                    window.OcaTextValueBox ? <window.OcaTextValueBox label={title} value={val} config={node} /> : <span>{val}</span>
                )}
            </div>
        );
    }

    if (type.toLowerCase().includes('link') || type === '_WebLink') {
        return (
            <div style={style}>
                {window.OcaWebLink ? <window.OcaWebLink config={node} /> : <a href="#">{title}</a>}
            </div>
        );
    }

    return (
        <div className="mock-widget" style={{padding: '10px', background: '#222', border: '1px solid #333', borderRadius: '4px'}}>
            <div style={{fontSize: '9px', color: '#666'}}>{node.type}</div>
            <div style={{color: '#aaa', fontWeight: 'bold'}}>{nodeName}</div>
        </div>
    );
};
