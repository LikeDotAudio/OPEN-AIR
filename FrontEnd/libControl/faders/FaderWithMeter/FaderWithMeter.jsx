/**
 * Header: FaderWithMeter.jsx
 * Purpose: FaderWithMeter component or utility.
 * Description: Handles logic and rendering for FaderWithMeter component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// Inline comment: Logic for FaderWithMeter
const FaderWithMeter = ({ value, onChange, config }) => {
    const title = config?.label?.[window.useMqttLang()[0]] || config?.label_active?.[window.useMqttLang()[0]] || "";
    
    // Geometry
    const w = config?.layout?.width || 120;
    const h = config?.layout?.height || 300;
    
    const meterWidth = config?.meter_width || 12;
    const faderWidth = config?.fader_width || 40;
    const barEnable = config?.bar_enable !== false;

    // Sub-configs
    const faderConfig = {
        ...config,
        geometry: { ...config?.geometry, width: faderWidth, height: h - 40 },
        show_label: false,
        show_value: true
    };

    // Meters usually track a different MQTT topic, but for the Zoo we can mirror the fader
    // or provide dummy data.
    const meterConfig = {
        ...config,
        geometry: { width: meterWidth, height: h - 60 },
        cosmetics: {
            colors: {
                primary: '#0f0',
                warning: '#ff0',
                danger: '#f00',
                background: '#111'
            }
        }
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '5px' }}>
            {title && <div style={{ fontSize: '10px', color: '#aaa', fontWeight: 'bold' }}>{title.toUpperCase()}</div>}
            
            <div style={{ 
                display: 'flex', 
                flexDirection: 'row', 
                alignItems: 'center', 
                backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, '#2b2b2b') : '#2b2b2b'), 
                padding: '10px', 
                borderRadius: '4px',
                border: '1px solid #111',
                gap: '8px'
            }}>
                {/* Left Meter */}
                {barEnable && window.MeterBarGraph && (
                    <window.MeterBarGraph value={value} config={config?.left_meter_style ? {...meterConfig, cosmetics: {colors: {primary: config.left_meter_style.lower_range_colour || '#0f0'}}} : meterConfig} />
                )}

                {/* Central Fader */}
                {window.Fader && <window.Fader value={value} onChange={onChange} config={faderConfig} />}

                {/* Right Meter */}
                {barEnable && window.MeterBarGraph && (
                    <window.MeterBarGraph value={value} config={config?.right_meter_style ? {...meterConfig, cosmetics: {colors: {primary: config.right_meter_style.lower_range_colour || '#0f0'}}} : meterConfig} />
                )}
            </div>
        </div>
    );
};

window.FaderWithMeter = FaderWithMeter;