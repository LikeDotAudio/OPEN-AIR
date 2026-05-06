/**
 * Structural Component: OcaBin
 * A high-level container that manages background effects and scrolling.
 */
window.OcaBin = ({ nodeName, node, path_prefix }) => {
  const overflowEW = node.behavior?.overflow_ew === 'auto' ? 'auto' : 'hidden';
  const overflowNS = node.behavior?.overflow_ns === 'auto' ? 'auto' : 'hidden';

  return (
    <div className="oca-bin" style={{ 
        width: '100%', 
        height: '100%', 
        overflowX: overflowEW, 
        overflowY: overflowNS,
        backgroundColor: '#121212',
        position: 'relative',
        padding: '0px',
        boxSizing: 'border-box'
    }}>
      {node.blocks && typeof node.blocks === 'object' && Object.entries(node.blocks).map(([k, v]) => (
        <window.WidgetFactory key={k} nodeName={k} node={v} path_prefix={`${path_prefix}/${nodeName}`} />
      ))}
      {node.fields && typeof node.fields === 'object' && Object.entries(node.fields).map(([k, v]) => (
        <window.WidgetFactory key={k} nodeName={k} node={v} path_prefix={`${path_prefix}/${nodeName}`} />
      ))}
    </div>
  );
};

/**
 * Structural Component: OcaBlock
 * A grouped set of controls with a grid layout.
 */
window.OcaBlock = ({ nodeName, node, path_prefix }) => {
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
          <window.WidgetFactory key={k} nodeName={k} node={v} path_prefix={`${path_prefix}/${nodeName}`} />
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
window.WidgetFactory = ({ nodeName, node, path_prefix = '' }) => {
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
  };

  if (!ComponentToRender) {
    if (node.type && (
        node.type.startsWith('_') || 
        node.type.toLowerCase().includes('fader') || 
        node.type.toLowerCase().includes('meter') || 
        node.type.toLowerCase().includes('button') ||
        node.type.toLowerCase().includes('actuator') ||
        node.type.toLowerCase().includes('checkbox') ||
        node.type.toLowerCase().includes('value') ||
        node.type.toLowerCase().includes('label')
    )) {
        return (
            <div style={gridStyles} className={`widget-wrapper ${node.type}`}>
                <window.FieldComponent nodeName={nodeName} node={node} path_prefix={path_prefix} />
            </div>
        );
    }
    return (
        <div style={{ border: '1px dashed #333', padding: '5px', margin: '2px' }}>
            {node.blocks && typeof node.blocks === 'object' && Object.entries(node.blocks).map(([k, v]) => (
                <window.WidgetFactory key={k} nodeName={k} node={v} path_prefix={`${path_prefix}/${nodeName}`} />
            ))}
            {node.fields && typeof node.fields === 'object' && Object.entries(node.fields).map(([k, v]) => (
                <window.WidgetFactory key={k} nodeName={k} node={v} path_prefix={`${path_prefix}/${nodeName}`} />
            ))}
        </div>
    );
  }

  // 4. Render the registered component
  return (
    <div style={gridStyles} className={`widget-wrapper ${node.type}`}>
      <ComponentToRender 
        nodeName={nodeName}
        node={node} 
        path_prefix={path_prefix}
      />
    </div>
  );
};

window.FieldComponent = ({ nodeName, node, path_prefix }) => {
    const topic = `OpenAir/Gui${path_prefix}/${nodeName}`;
    
    // Determine default value
    let defaultVal = 0;
    if (node.domain?.primary?.value_default !== undefined) {
        defaultVal = node.domain.primary.value_default;
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

    const style = { display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%', height: '100%' };
    const titleStyle = { fontSize: '12px', color: node.cosmetics?.colors?.text || '#999', marginBottom: '10px' };

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

    if (type === '_CompositeFader' || type === '_GCA' || type === 'GCA') {
        return (
            <div style={style}>
                {window.GCA ? <window.GCA value={val} onChange={setVal} config={node} /> : <div style={{width: '100px', height: '150px', background: '#333'}}>GCA</div>}
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
                {window.Fader ? <window.Fader value={val} onChange={setVal} config={node} /> : <div style={{width: '30px', height: '150px', background: '#444'}}></div>}
            </div>
        );
    }

    if (type.toLowerCase().includes('meter')) {
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
                {Widget ? <Widget value={val} onChange={setVal} config={node} size={100}/> : <div style={{width: '100px', height: '100px', borderRadius:'50%', background: '#444'}}></div>}
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

    if (type.toLowerCase().includes('button') || type.toLowerCase().includes('actuator')) {
        const isWink = type.toLowerCase().includes('wink');
        const isTrapezoid = type.toLowerCase().includes('trapezoid');
        const isToggle = type.toLowerCase().includes('toggle') || isWink || isTrapezoid;
        
        // Handle Toggler with multiple options (Grid of buttons)
        if (node.options && typeof node.options === 'object' && Object.keys(node.options).length > 1) {
            const maxCols = node.layout?.max_cols || 1;
            const options = Object.entries(node.options).map(([k, v]) => ({ ...v, key: k }));
            
            return (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', width: '100%' }}>
                    {title && <div style={{ fontSize: '11px', color: '#666', fontWeight: 'bold' }}>{title}</div>}
                    <div style={{ 
                        display: 'grid', 
                        gridTemplateColumns: `repeat(${maxCols}, 1fr)`, 
                        gap: '5px' 
                    }}>
                        {options.map((opt) => {
                            const optTitle = getLocalizedLabel(opt.label) || getLocalizedLabel(opt.label_active) || opt.key;
                            const isOptActive = val === opt.value || val === opt.key;
                            
                            return (
                                <div key={opt.key}>
                                    {isWink ? (
                                        window.OcaWinkButton && <window.OcaWinkButton label={optTitle} value={isOptActive} onChange={() => setVal(opt.value || opt.key)} config={{...node, ...opt}} />
                                    ) : isTrapezoid ? (
                                        window.OcaTrapezoidButton && <window.OcaTrapezoidButton label={optTitle} value={isOptActive} onChange={() => setVal(opt.value || opt.key)} config={{...node, ...opt}} />
                                    ) : (
                                        window.OcaToggleButton && <window.OcaToggleButton label={optTitle} value={isOptActive} onChange={() => setVal(opt.value || opt.key)} config={{...node, ...opt}} />
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>
            );
        }

        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '10px' }}>
                {isWink ? (
                    window.OcaWinkButton ? <window.OcaWinkButton label={title} value={val} onChange={setVal} config={node} /> : <button>{title}</button>
                ) : isTrapezoid ? (
                    window.OcaTrapezoidButton ? <window.OcaTrapezoidButton label={title} value={val} onChange={setVal} config={node} /> : <button>{title}</button>
                ) : isToggle ? (
                    window.OcaToggleButton ? <window.OcaToggleButton label={title} value={val} onChange={setVal} /> : <button>{title}</button>
                ) : (
                    window.OcaButton ? <window.OcaButton label={title} onClick={() => setVal(val === 1 ? 0 : 1)} /> : <button>{title}</button>
                )}
            </div>
        );
    }

    if (type.toLowerCase().includes('checkbox')) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '10px' }}>
                {window.OcaCheckbox ? <window.OcaCheckbox label={title} checked={val} onChange={setVal} /> : <input type="checkbox" />}
            </div>
        );
    }

    if (type.toLowerCase().includes('listbox') || type.toLowerCase().includes('dropdown')) {
        const options = node.options || ['Option 1', 'Option 2'];
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '10px' }}>
                {window.OcaDropdown ? <window.OcaDropdown label={title} value={val} onChange={setVal} options={options} /> : <select><option>{title}</option></select>}
            </div>
        );
    }

    if (type.toLowerCase().includes('label')) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '10px' }}>
                {window.OcaTextLabel ? <window.OcaTextLabel label={title} color={node.cosmetics?.colors?.text || '#ccc'} /> : <span>{title}</span>}
            </div>
        );
    }

    if (type.toLowerCase().includes('value')) {
        const units = node.unit_text || node.units || '';
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '10px' }}>
                {window.OcaTextValueBox ? <window.OcaTextValueBox label={title} value={val} units={units} /> : <span>{val} {units}</span>}
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