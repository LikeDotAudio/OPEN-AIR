/**
 * VUMeterKnob - Composite Meter + Knob Component
 * Author: Anthony Peter Kuzub / Gemini (Collaborator)
 * Version: 20260506.2200.2
 *
 * Description: High-fidelity composite component featuring a NeedleMeter with a Knob at its pivot.
 */

const VUMeterKnob = ({ value, onChange, config, topic, path_prefix }) => {
    // --- 1. Config Splitting & Inheritance ---
    const c = config || {};
    const useMqttLang = window.useMqttLang || (() => ['En', () => {}]);
    const [lang] = useMqttLang();

    // Clone config for Knob and VU
    const vuConfig = { ...c };
    const knobConfig = { ...c };

    // Process knob_ overrides
    Object.entries(c).forEach(([k, v]) => {
        if (k.startsWith('knob_')) {
            const newK = k.replace('knob_', '');
            knobConfig[newK] = v;
        }
    });

    // Forced aesthetics
    knobConfig.show_label = false;
    knobConfig.width = c.knob_width || 60;
    knobConfig.height = c.knob_height || 60;
    vuConfig.meter_face_colour = c.meter_face_colour || 'transparent';

    // --- 2. Multi-Topic State Management ---
    const useMqttState = window.useMqttState || React.useState;
    const knobTopic = c.knob_path ? `OpenAir/Gui${path_prefix}/${c.knob_path}` : null;
    
    const [knobVal, setKnobVal] = knobTopic ? useMqttState(knobTopic, c.knob_value_default || 0, knobConfig) : [0, () => {}];

    // --- 3. Layout & Geometry ---
    const size = c.size || 150;
    const width = c.geometry?.width || c.width || size;
    const height = c.geometry?.height || c.height || size;

    // Center pivot (from NeedleMeter standard)
    const styleOv = vuConfig.cosmetics?.style_overrides || {};
    const centerX = width / 2 + (styleOv.pivot_offset_x || 0);
    const centerY = height / 2 + (styleOv.pivot_offset_y || 0);

    return (
        <div className="vu-meter-knob-composite" style={{ 
            width, height, 
            position: 'relative', 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center' 
        }}>
            {/* Base Layer: VU Meter */}
            <div style={{ position: 'absolute', top: 0, left: 0, zIndex: 1 }}>
                {window.NeedleMeter && <window.NeedleMeter value={value} config={vuConfig} />}
            </div>

            {/* Top Layer: Knob at Pivot */}
            <div style={{ 
                position: 'absolute', 
                left: centerX, 
                top: centerY, 
                transform: 'translate(-50%, -50%)', 
                zIndex: 10 
            }}>
                {window.Knob && (
                    <window.Knob 
                        value={knobVal} 
                        onChange={setKnobVal} 
                        config={knobConfig} 
                        size={knobConfig.width} 
                    />
                )}
            </div>
        </div>
    );
};

window.VUMeterKnob = VUMeterKnob;
