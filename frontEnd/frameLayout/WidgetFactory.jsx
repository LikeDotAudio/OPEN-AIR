// Convert a layout value to a CSS length: number or numeric-string -> px,
// "%"/other CSS strings pass through. Lets width/height be entered as px OR %.
window.oaCssLen = (v) => {
  if (v == null) return null;
  if (typeof v === 'number') return `${v}px`;
  const s = String(v).trim();
  return /^-?\d+(\.\d+)?$/.test(s) ? `${s}px` : s;
};

/**
 * Structural Component: OcaBin
 * A high-level container that manages background effects and scrolling.
 */
window.OcaBin = ({ nodeName, node, path_prefix, jsonPath }) => {
  const overflowEW = node.behavior?.overflow_ew === 'auto' ? 'auto' : 'hidden';
  const overflowNS = node.behavior?.overflow_ns === 'auto' ? 'auto' : 'hidden';

  return (
    <div className="oca-bin" style={{
        width: '100%',
        height: '100%',
        // Flex column so child blocks stack and the bin actually fills the
        // NSEW space declared in geometry. overflow_ns/ew then only scroll
        // when content genuinely exceeds the pane ("auto overflow as needed").
        display: 'flex',
        flexDirection: 'column',
        minHeight: 0,
        overflowX: overflowEW,
        overflowY: overflowNS,
        backgroundColor: '#121212',
        position: 'relative',
        padding: '0px',
        boxSizing: 'border-box'
    }}>
      {node.blocks && typeof node.blocks === 'object' && Object.entries(node.blocks).map(([k, v]) => (
        <window.WidgetFactory key={k} nodeName={k} node={v} path_prefix={`${path_prefix}/${nodeName}`} jsonPath={jsonPath ? `${jsonPath}.blocks.${k}` : undefined} />
      ))}
      {node.fields && typeof node.fields === 'object' && Object.entries(node.fields).map(([k, v]) => (
        <window.WidgetFactory key={k} nodeName={k} node={v} path_prefix={`${path_prefix}/${nodeName}`} jsonPath={jsonPath ? `${jsonPath}.fields.${k}` : undefined} />
      ))}
    </div>
  );
};

/**
 * Structural Component: OcaBlock
 * A grouped set of controls with a grid layout.
 */
window.OcaBlock = ({ nodeName, node, path_prefix, jsonPath }) => {
  const [lang] = window.useMqttLang();
  const cols = node.layout_columns || 1;
  const title = node.description?.[lang] || node.description?.En || nodeName;

  return (
    <div className="oca-block" style={{
        margin: '0px',
        border: '1px solid #222',
        backgroundColor: '#1e1e1e',
        padding: '5px',
        borderRadius: '2px'
    }}>
      <div style={{ color: '#888', fontSize: '10px', borderBottom: '1px solid #222', marginBottom: '5px', fontWeight: 'bold', opacity: 0.8 }}>
        {title.toUpperCase()}
      </div>
      <div style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${cols}, 1fr)`,
          gap: '5px'
      }}>
        {node.fields && typeof node.fields === 'object' && Object.entries(node.fields).map(([k, v]) => (
          <window.WidgetFactory key={k} nodeName={k} node={v} path_prefix={`${path_prefix}/${nodeName}`} jsonPath={jsonPath ? `${jsonPath}.fields.${k}` : undefined} />
        ))}
      </div>
    </div>
  );
};

/**
 * WidgetFactory: The recursive engine that translates JSON schema definitions 
 * into a dynamic React component tree. Handles component registry lookups, 
 * layout attribute mapping, and fallback rendering for unregistered types.
 */
window.WidgetFactory = ({ nodeName, node, path_prefix = '', jsonPath }) => {
  if (!node) return null;

  const COMPONENT_REGISTRY = {
    'OcaBin': window.OcaBin,
    'OcaBlock': window.OcaBlock,
    'OcaNotebook': window.TabLayout,
    'OcaSplit': window.SplitLayout,
    'OcaTable': window.OcaTable,
  };

  const ComponentToRender = COMPONENT_REGISTRY[node.type];

  // Map JSON layout constraints to CSS Grid attributes for reactive container sizing
  const gridStyles = {
    gridColumnStart: node.layout?.column !== undefined ? node.layout.column : 'auto',
    gridRowStart: node.layout?.row !== undefined ? node.layout.row : 'auto',
    gridColumnEnd: node.layout?.col_span ? `span ${node.layout.col_span}` : 'auto',
    gridRowEnd: node.layout?.row_span ? `span ${node.layout.row_span}` : 'auto',
    // Flex semantics for when this widget is the child of a flex container
    // (e.g. an OcaBin column). 'weight' mirrors the desktop Tk grid weight:
    // 0 = size to content, >0 = grow to share leftover space. flexShrink:0
    // keeps content from being squished, which previously made stacked widgets
    // overlap their neighbours.
    flexGrow: node.layout?.weight !== undefined ? node.layout.weight : 0,
    flexShrink: 0,
    // Tk grid padx/pady -> external spacing around the element within its cell.
    // box-sizing keeps the padding from overflowing fill containers.
    ...((node.layout?.padx != null || node.layout?.pady != null)
      ? { padding: `${node.layout?.pady ?? 0}px ${node.layout?.padx ?? 0}px`, boxSizing: 'border-box' }
      : {}),
  };

  // Containers declared NSEW must fill their parent so 'overflow: auto' only
  // scrolls when content truly exceeds the pane. The wrapper previously had no
  // height, collapsing every nested container to content height and breaking
  // the height:100% chain from the pane down to the OcaBin.
  const FILL_CONTAINERS = ['OcaBin', 'OcaNotebook', 'OcaSplit', 'OcaTable'];

  if (!ComponentToRender) {
    if (node.type && (
        node.type.startsWith('_') || 
        node.type.toLowerCase().includes('fader') || 
        node.type.toLowerCase().includes('meter') || 
        node.type.toLowerCase().includes('button') ||
        node.type.toLowerCase().includes('actuator') ||
        node.type.toLowerCase().includes('checkbox') ||
        node.type.toLowerCase().includes('value') ||
        node.type.toLowerCase().includes('label') ||
        node.type.toLowerCase().includes('graph') ||
        node.type.toLowerCase().includes('plot') ||
        node.type.toLowerCase().includes('link')
    )) {
        return (
            <div style={gridStyles} className={`widget-wrapper ${node.type}`} data-oca-path={jsonPath}>
                <window.FieldComponent nodeName={nodeName} node={node} path_prefix={path_prefix} />
            </div>
        );
    }
    return (
        <div style={{ border: '1px dashed #333', padding: '5px', margin: '2px' }} data-oca-path={jsonPath}>
            {node.blocks && typeof node.blocks === 'object' && Object.entries(node.blocks).map(([k, v]) => (
                <window.WidgetFactory key={k} nodeName={k} node={v} path_prefix={`${path_prefix}/${nodeName}`} jsonPath={jsonPath ? `${jsonPath}.blocks.${k}` : undefined} />
            ))}
            {node.fields && typeof node.fields === 'object' && Object.entries(node.fields).map(([k, v]) => (
                <window.WidgetFactory key={k} nodeName={k} node={v} path_prefix={`${path_prefix}/${nodeName}`} jsonPath={jsonPath ? `${jsonPath}.fields.${k}` : undefined} />
            ))}
        </div>
    );
  }

  // 4. Render the registered component
  let wrapperStyle = FILL_CONTAINERS.includes(node.type)
    ? { ...gridStyles, height: '100%', minHeight: 0, display: 'flex', flexDirection: 'column' }
    : gridStyles;

  // Explicit width/height (percent string or px number), e.g. set by the WYSIWYG
  // editor's resize handles. Only applied when present, so existing containers
  // that don't declare a size keep their fill/auto behavior.
  const _lw = node.layout?.width, _lh = node.layout?.height;
  if (_lw != null || _lh != null) {
    wrapperStyle = { ...wrapperStyle };
    if (_lw != null) wrapperStyle.width = window.oaCssLen(_lw);
    if (_lh != null) { wrapperStyle.height = window.oaCssLen(_lh); wrapperStyle.minHeight = 0; }
  }

  return (
    <div style={wrapperStyle} className={`widget-wrapper ${node.type}`} data-oca-path={jsonPath}>
      <ComponentToRender
        nodeName={nodeName}
        node={node}
        path_prefix={path_prefix}
        jsonPath={jsonPath}
      />
    </div>
  );
};

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
    } : rawNode;

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

    if (type === '_VUMeterKnob') {
        return (
            <div style={style}>
                {window.VUMeterKnob ? <window.VUMeterKnob value={val} onChange={setVal} config={node} topic={topic} path_prefix={path_prefix} /> : <div style={{width: '150px', height: '150px', background: '#333'}}>VU Knob</div>}
            </div>
        );
    }

    if (type.toLowerCase().includes('meter') || type === '_BarGraph' || type === '_SmartMeter' || type === '_Meter') {
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

    if (type.toLowerCase().includes('status_light') || type.toLowerCase().includes('indicator')) {
        return (
            <div style={style}>
                {window.StatusLight ? <window.StatusLight value={val} config={node} /> : <div style={{width: '15px', height: '15px', borderRadius: '50%', background: 'red'}}></div>}
            </div>
        );
    }

    if (type.toLowerCase().includes('image_display') || type.toLowerCase().includes('picture')) {
        return (
            <div style={style}>
                {window.ImageDisplay ? <window.ImageDisplay value={val} config={node} /> : <div style={{background: '#222', color: '#fff'}}>Image</div>}
            </div>
        );
    }

    if (type.toLowerCase().includes('break_line') || type.toLowerCase().includes('separator')) {
        return (
            <div style={style}>
                {window.BreakLine ? <window.BreakLine config={node} /> : <hr />}
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
            return (
                <div style={{ ...style, width: pw != null ? `${pw * 100}%` : '100%', height: 'auto' }}>
                    {window.ButtonToggler ? <window.ButtonToggler value={val} onChange={setVal} config={node} topic={topic} nodeJson={node} /> : <div style={{background: '#333'}}>Button Toggler</div>}
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

    if (type.toLowerCase().includes('listbox') || type.toLowerCase().includes('dropdown') || type === '_Listbox') {
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

    if (type.toLowerCase().includes('value') || type === '_TextInput' || type === '_SliderValue') {
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