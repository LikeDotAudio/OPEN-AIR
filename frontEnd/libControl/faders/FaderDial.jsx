const FaderDial = ({ value, onChange, config }) => {
    // Parsing configuration
    const title = config?.label?.En || config?.label_active?.En || "Composite";
    const min = config?.domain?.primary?.min !== undefined ? config.domain.primary.min : 0;
    const max = config?.domain?.primary?.max !== undefined ? config.domain.primary.max : 100;
    const units = config?.units || config?.unit_text || "";
    
    // Step configuration
    const stepCoarse = config?.step_coarse || 1.0;
    const stepFine = config?.step_fine || config?.step || 0.01;

    // Component states
    const [inputValue, setInputValue] = React.useState((value !== undefined ? value : min).toFixed(2));
    
    React.useEffect(() => {
        setInputValue((value !== undefined ? value : min).toFixed(2));
    }, [value]);

    const handleTextChange = (e) => {
        setInputValue(e.target.value);
    };

    const handleTextBlur = () => {
        let parsed = parseFloat(inputValue);
        if (!isNaN(parsed)) {
            parsed = Math.max(min, Math.min(max, parsed));
            // Round to fine step
            const rounded = Math.round(parsed / stepFine) * stepFine;
            onChange(rounded);
            setInputValue(rounded.toFixed(2));
        } else {
            setInputValue((value !== undefined ? value : min).toFixed(2));
        }
    };

    const handleTextKeyDown = (e) => {
        if (e.key === 'Enter') {
            handleTextBlur();
            e.target.blur();
        }
    };

    // Sub-configs
    const faderConfig = {
        ...config,
        ...config?.fader_config,
        geometry: { ...config?.geometry, orientation: 'horizontal', width: 250, height: 40 },
        show_value: false,
        show_label: false
    };

    const knobConfig = {
        ...config,
        ...config?.dial_config,
        geometry: { width: 60, height: 60 },
        style: { ...config?.style, knob_style: 'dial' },
        readout: { show_label: false, text_inside: false },
        domain: { primary: { min: 0, max: 999 } }
    };

    // When the knob moves, it acts as an endless encoder adding/subtracting stepFine
    // Our Knob component returns absolute values. We need to calculate deltas.
    const lastKnobRef = React.useRef(0);
    const handleKnobChange = (newKnobVal) => {
        const delta = newKnobVal - lastKnobRef.current;
        lastKnobRef.current = newKnobVal;
        
        // If it wrapped around (0 to 999 or 999 to 0)
        let actualDelta = delta;
        if (delta > 500) actualDelta -= 999;
        if (delta < -500) actualDelta += 999;

        const currentVal = value !== undefined ? value : min;
        let nextVal = currentVal + (actualDelta * stepFine * 10); // scale up sensitivity slightly
        nextVal = Math.max(min, Math.min(max, nextVal));
        
        onChange(Math.round(nextVal / stepFine) * stepFine);
    };

    return (
        <div style={{ 
            display: 'flex', 
            flexDirection: 'row', 
            alignItems: 'center', 
            backgroundColor: '#2b2b2b', 
            padding: '10px', 
            borderRadius: '4px',
            border: '1px solid #111',
            gap: '15px',
            width: 'fit-content'
        }}>
            {/* Left Block: Label & Fader */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                <div style={{ fontSize: '10px', color: '#888', fontWeight: 'bold', textTransform: 'uppercase', paddingLeft: '5px' }}>
                    {title}
                </div>
                {window.Fader && <window.Fader value={value} onChange={onChange} config={faderConfig} />}
            </div>

            {/* Middle Block: Dial Knob */}
            <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                {window.Knob && <window.Knob value={lastKnobRef.current} onChange={handleKnobChange} config={knobConfig} />}
            </div>

            {/* Right Block: Input Value & Units */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '5px' }}>
                <input 
                    type="text" 
                    value={inputValue}
                    onChange={handleTextChange}
                    onBlur={handleTextBlur}
                    onKeyDown={handleTextKeyDown}
                    style={{
                        width: '50px',
                        backgroundColor: '#111',
                        color: '#fff',
                        border: '1px inset #222',
                        padding: '5px',
                        textAlign: 'center',
                        fontFamily: 'monospace',
                        borderRadius: '3px',
                        outline: 'none'
                    }}
                />
                <div style={{ fontSize: '9px', color: '#888' }}>
                    {units}
                </div>
            </div>
        </div>
    );
};

window.FaderDial = FaderDial;