// HighVisButton Component
// A button with a thick, high-visibility outer rim and a dark inner pushable area.

const HighVisButton = ({ value, onChange, config, topic, nodeJson }) => {
    const useMqtt = !!topic;
    const useMqttState = window.useMqttState || React.useState;
    const initialIsOn = config?.options?.ON?.selected || false;
    const [val, setVal] = useMqtt ? useMqttState(topic, value !== undefined ? value : initialIsOn, nodeJson) : [value !== undefined ? value : initialIsOn, onChange, 'En'];
    const [lang] = window.useMqttLang ? window.useMqttLang() : ['En'];

    const getLocalizedText = (labelData, fallback) => {
        if (!labelData) return fallback;
        if (typeof labelData === 'string') return labelData;
        return labelData[lang] || labelData.En || fallback;
    };

    const label = getLocalizedText(config?.label, "");
    const onText = getLocalizedText(config?.label_active, label || "ON");
    const offText = getLocalizedText(config?.label_inactive, label || "OFF");

    const layout = config?.layout || {};
    const width = config?.geometry?.width || layout.width || 80;
    const height = config?.geometry?.height || layout.height || 45;
    
    // Shape logic: pill vs rect
    const shape = config?.cosmetics?.shape || config?.shape || 'rect'; // 'rect' or 'pill'
    const isPill = shape === 'pill';
    const cornerRadius = isPill ? height / 2 : (config?.geometry?.corner_radius || layout.corner_radius || 8);
    const innerCornerRadius = isPill ? (height - 6) / 2 : Math.max(2, cornerRadius - 3);

    const styleObj = config?.style || {};
    const A = styleObj.active || {};
    const I = styleObj.inactive || {};
    
    const pk = (...vals) => vals.find((v) => v !== undefined && v !== null);

    const grpActive = {
        text_color: pk(A.text_color, styleObj.active_text_color, '#FF7755'),
        inner_bg_color: pk(A.inner_bg_color, styleObj.active_inner_bg_color, '#222222'),
        rim_color: pk(A.rim_color, styleObj.active_rim_color, '#ffffff'),
        font_style: pk(A.font_style, styleObj.active_font_style, 'bold'),
        font_size: pk(A.font_size, styleObj.active_font_size, 12),
        glow_intensity: pk(A.glow_intensity, styleObj.glow_intensity, 5),
    };
    
    const grpInactive = {
        text_color: pk(I.text_color, styleObj.text_color, '#cccccc'),
        inner_bg_color: pk(I.inner_bg_color, styleObj.inner_bg_color, '#2a2a2a'),
        rim_color: pk(I.rim_color, styleObj.rim_color, '#999999'),
        font_style: pk(I.font_style, styleObj.inactive_font_style, 'bold'),
        font_size: pk(I.font_size, styleObj.inactive_font_size, 12),
        glow_intensity: pk(I.glow_intensity, 0),
    };

    const isHovered = React.useRef(false);
    const [hoverState, setHoverState] = React.useState(false);
    const [isPressed, setIsPressed] = React.useState(false);

    const s = val ? grpActive : grpInactive;
    const currentText = val ? onText : offText;
    
    const glow = s.glow_intensity > 0 ? `0 0 ${s.glow_intensity}px ${s.rim_color}` : 'none';

    const handlePointerDown = (e) => {
        e.preventDefault(); // prevent selection
        setIsPressed(true);
    };

    const handlePointerUp = () => {
        if (isPressed) {
            setIsPressed(false);
            const newVal = !val;
            if (useMqtt) {
                setVal(newVal);
            } else if (onChange) {
                onChange(newVal);
            }
        }
    };

    const handlePointerLeave = () => {
        isHovered.current = false;
        setHoverState(false);
        setIsPressed(false);
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            {config?.show_label !== false && label && (
                <div style={{ fontSize: '10px', color: '#aaaaaa', fontWeight: 'bold', marginBottom: '4px', textTransform: 'uppercase' }}>
                    {label}
                </div>
            )}
            
            {/* Outer Rim Container */}
            <div 
                onPointerDown={handlePointerDown}
                onPointerUp={handlePointerUp}
                onPointerEnter={() => { isHovered.current = true; setHoverState(true); }}
                onPointerLeave={handlePointerLeave}
                style={{
                    width: `${width}px`,
                    height: `${height}px`,
                    backgroundColor: s.rim_color,
                    borderRadius: `${cornerRadius}px`,
                    padding: '3px', // Thickness of the rim
                    boxSizing: 'border-box',
                    boxShadow: glow,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    userSelect: 'none',
                    transition: 'all 0.1s ease',
                    transform: isPressed ? 'scale(0.96)' : (hoverState ? 'scale(1.02)' : 'scale(1)')
                }}
            >
                {/* Inner Button Container */}
                <div style={{
                    width: '100%',
                    height: '100%',
                    backgroundColor: s.inner_bg_color,
                    borderRadius: `${innerCornerRadius}px`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: '1px solid #111',
                    boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.5)',
                }}>
                    <span style={{
                        color: s.text_color,
                        fontWeight: s.font_style,
                        fontSize: `${s.font_size}px`,
                        letterSpacing: '0.5px',
                        textShadow: val ? `0 0 5px ${s.text_color}` : 'none',
                        transition: 'color 0.1s ease'
                    }}>
                        {currentText}
                    </span>
                </div>
            </div>
        </div>
    );
};

window.HighVisButton = HighVisButton;
