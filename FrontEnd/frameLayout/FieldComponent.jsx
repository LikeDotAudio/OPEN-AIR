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
    // active/inactive may now be { text:<string|{En,…}>, text_size, text_color }.
    // Unwrap to the wording for label_active/label_inactive (back-compat via
    // oaLabelText), and hoist the per-state text styling so widgets can honor it.
    const _txt = window.oaLabelText || ((s) => s);
    if (_labIsPair) {
        if (node.label_active === undefined) node.label_active = _txt(_lab.active);
        if (node.label_inactive === undefined) node.label_inactive = _txt(_lab.inactive !== undefined ? _lab.inactive : _lab.active);
        const _as = (_lab.active && typeof _lab.active === 'object') ? _lab.active : null;
        const _is = (_lab.inactive && typeof _lab.inactive === 'object') ? _lab.inactive : _as;
        if (_as && node.label_text_size === undefined && _as.text_size !== undefined) node.label_text_size = _as.text_size;
        if (_as && node.label_text_color === undefined && _as.text_color !== undefined) node.label_text_color = _as.text_color;
        if (_is && node.label_inactive_text_size === undefined && _is.text_size !== undefined) node.label_inactive_text_size = _is.text_size;
        if (_is && node.label_inactive_text_color === undefined && _is.text_color !== undefined) node.label_inactive_text_color = _is.text_color;
    }

    // show_label now lives under label (migrated from top-level / style_flags /
    // labels). Hoist it to the node level so widgets that read config.show_label
    // (e.g. MeterBarGraph) keep working without per-widget changes.
    if (_lab && typeof _lab === 'object' && _lab.show_label !== undefined && node.show_label === undefined) {
        node.show_label = _lab.show_label;
    }

    // path_prefix is set by LoaderOrchestrator to the full file-derived prefix
    // (e.g. "OpenAir/Gui/Window/Spectrum/Instrument/frequency"), mirroring
    // Python's generate_topic_path_from_filepath. nodeName is the leaf
    // identifier; when empty (root passthrough), the prefix IS the topic.
    const topic = nodeName ? `${path_prefix}/${nodeName}` : path_prefix;

    // Determine default value. The canonical value pillar is value.default_value
    // (checked first); domain.primary.value_default and flat value_default are
    // legacy fallbacks.
    let defaultVal = 0;
    if (node.value?.default_value !== undefined) {
        defaultVal = node.value.default_value;
    } else if (node.domain?.primary?.value_default !== undefined) {
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
        node.label = getLocalizedLabel(_txt(_lab.text)) || getLocalizedLabel(_txt(_lab.active)) || getLocalizedLabel(_txt(_lab.inactive)) || '';
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

    // Procedural Panel cover (WASM). Placed explicitly in a layout as a sized
    // background tile; the engine auto-places its own screws.
    if (type === 'panel' || type === 'Panel' || type.toLowerCase() === 'oapanel') {
        return (
            <div style={style}>
                {window.Panel ? <window.Panel node={node} config={node.cosmetics?.panel || node.panel} /> : <div style={{width: '100%', height: '100%', background: '#2a2a2a'}}></div>}
            </div>
        );
    }

    // Standalone procedural screw (WASM). The Panel cover fastens its own; this
    // is for dropping a single screw on its own.
    if (type === 'Spacer') {
        const w = window.oaCssLen(node.geometry?.width || 0);
        const h = window.oaCssLen(node.geometry?.height || 0);
        return <div style={{width: w, height: h, display: 'inline-block'}}></div>;
    }
    
    if (type === '_AudioAnalyzerDemo') {
        return (
            <div style={style}>
                {window.AudioAnalyzerDemo ? <window.AudioAnalyzerDemo config={node} /> : null}
            </div>
        );
    }
    
    if (type === 'screw' || type === 'Screw') {
        return (
            <div style={{ ...style, height: 'auto' }}>
                {window.Screw ? <window.Screw node={node} config={node.cosmetics?.screw || node.screw} /> : <div style={{width: 24, height: 24, borderRadius: '50%', background: '#888'}}></div>}
            </div>
        );
    }

    // GCA — Ganged Controlled Array: N parallel channel tracks + master cap.
    // The reference is oaGuiElements/Core/faders/fader_ganged_controlled_array/index.htm.
    if (type === '_GCA' || type === 'GCA' || type.toLowerCase().includes('ganged')) {
        return (
            <div style={style}>
                {window.GCA ? <window.GCA value={val} onChange={setVal} config={node} /> : <div style={{width: '200px', height: '400px', background: '#222'}}></div>}
            </div>
        );
    }

    // _Horizontal_with_dial_Value is the canonical horizontal fader with the
    // value displayed in a dial. Composite/dial-value labels still route here.
    if (type.toLowerCase().includes('composite') || type.toLowerCase().includes('dial_value') || type === '_Horizontal_with_dial_Value') {
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

        // The rotary Knob fits its GRID CELL (like the Python canvas does): fill the
        // cell width, cap at the configured geometry size, and run fluid so the SVG
        // re-measures + redraws crisply at the cell size instead of overflowing at a
        // fixed 200px. SelectorSwitch/CMDP/MDP size themselves and are left as-is.
        const isRotaryKnob = Widget === window.Knob;
        const knobMax = window.oaCssLen(node.geometry?.width || node.layout?.width || 200);
        const knobWrapStyle = isRotaryKnob
            ? { ...style, width: '100%', maxWidth: knobMax, alignItems: 'center' }
            : style;
        const knobCfg = isRotaryKnob ? { ...fluidConfig, fluid: true } : fluidConfig;

        return (
            <div style={knobWrapStyle}>
                <span style={titleStyle}>{title}</span>
                {Widget ? <Widget value={val} onChange={setVal} config={knobCfg} size={100}/> : <div style={{width: '100px', height: '100px', borderRadius:'50%', background: '#444'}}></div>}
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
        if (type === '_MidiMessageLog') {
            return (
                <div style={style}>
                    {window.MidiMessageLog ? <window.MidiMessageLog value={val} config={node} /> : <div style={{background: '#222', color: '#fff'}}>MIDI Log</div>}
                </div>
            );
        }
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

    if (type === 'DynamicGraph' || type === 'plot_widget' || type === '_AudioDynamics' || type === '_Equalization' || type.toLowerCase().includes('graph')) {
        return (
            <div style={style}>
                {type === '_AudioDynamics' ? (
                    window.AudioDynamics ? <window.AudioDynamics value={val} config={node} topic={topic} nodeJson={node} /> : <div style={{width: '100%', height: '300px', background: '#222'}}>AudioDynamics Component</div>
                ) : type === '_Equalization' ? (
                    window.Equalization ? <window.Equalization value={val} config={node} topic={topic} nodeJson={node} /> : <div style={{width: '100%', height: '300px', background: '#222'}}>Equalization Component</div>
                ) : (
                    window.DynamicGraph ? <window.DynamicGraph value={val} config={node} topic={topic} nodeJson={node} /> : <div style={{width: '100%', height: '300px', background: '#222'}}>Graph Component</div>
                )}
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
        const isHighVis = type.toLowerCase().includes('highvis');
        const isTogglerGroup = type.toLowerCase().includes('toggler') || (node.options && typeof node.options === 'object' && Object.keys(node.options).length > 1 && !isWink && !isTrapezoid && !isHighVis);
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
                ) : isHighVis ? (
                    window.HighVisButton ? <window.HighVisButton value={val} onChange={setVal} config={node} topic={topic} nodeJson={node} /> : <button>{title}</button>
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
                    ? <window.OcaDropdown label={title} value={val} onChange={setVal} options={node.options} config={node} />
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

    // Protocol config.ini viewer: fetches BackEnd/ComProtocols/openair-<proto>/
    // config.ini via /api/config and publishes it (retained) to OpenAir/System/Config/<proto>.
    if (type === 'ProtocolConfigDisplay' || type.toLowerCase().includes('protocolconfig')) {
        return (
            <div style={style}>
                {window.ProtocolConfigDisplay
                    ? <window.ProtocolConfigDisplay config={node} topic={topic} />
                    : <div className="mock-widget">ProtocolConfigDisplay (not loaded)</div>}
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
