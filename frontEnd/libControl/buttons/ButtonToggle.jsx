// ButtonToggle Component
// Author: Gemini (Collaborator)
// Version: 20260507.1000.1
//
// Description: Stateful toggle button component matching Python's ToggleButton.

const ButtonToggle = ({ value, onChange, config, topic, nodeJson }) => {
    const useMqtt = !!topic;
    const useMqttState = window.useMqttState;
    const initialIsOn = config?.options?.ON?.selected || false;
    const [val, setVal] = useMqtt ? useMqttState(topic, value !== undefined ? value : initialIsOn, nodeJson) : [value !== undefined ? value : initialIsOn, onChange, 'En'];
    const [lang] = window.useMqttLang ? window.useMqttLang() : ['En'];

    const getLocalizedText = (labelData, fallback) => {
        if (!labelData) return fallback;
        if (typeof labelData === 'string') return labelData;
        return labelData[lang] || labelData.En || fallback;
    };

    const label = getLocalizedText(config?.label, "Toggle");
    const onText = getLocalizedText(config?.label_active, label || "ON");
    const offText = getLocalizedText(config?.label_inactive, label || "OFF");

    const layout = config?.layout || {};
    const width = layout.width || 100;
    const height = layout.height || 50;
    const cornerRadius = layout.corner_radius || 6;
    
    const bgColor = config?.bg_color || "#1a1a1a";
    const activeColor = config?.active_color || "#FF9900";
    const activeBgColor = config?.active_bg_color || "#000000";
    const textColor = config?.text_color || "#888888";
    const activeTextColor = config?.active_text_color || "#1a1a1a";

    const isHovered = React.useRef(false);
    const [hoverState, setHoverState] = React.useState(false); 

    const currentText = val ? onText : offText;
    const currentBg = val ? activeBgColor : bgColor;
    const currentBorder = val ? activeColor : '#555';
    const currentTextColor = val ? activeTextColor : textColor;

    const handlePointerDown = () => {
        const newVal = !val;
        if (useMqtt) {
            setVal(newVal);
        } else if (onChange) {
            onChange(newVal);
        }
    };

    const handlePointerEnter = () => {
        isHovered.current = true;
        setHoverState(true);
    };

    const handlePointerLeave = () => {
        isHovered.current = false;
        setHoverState(false);
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            {label && (
                <div style={{ fontSize: '10px', color: 'white', fontWeight: 'bold', marginBottom: '4px' }}>
                    {label}
                </div>
            )}
            <div 
                style={{
                    width: `${width}px`,
                    height: `${height}px`,
                    backgroundColor: currentBg,
                    border: `2px solid ${isHovered.current ? (val ? activeColor : '#888') : currentBorder}`,
                    borderRadius: `${cornerRadius}px`,
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    cursor: 'pointer',
                    userSelect: 'none',
                    boxShadow: val ? `0 0 10px ${activeColor}80` : 'inset 0 0 5px rgba(0,0,0,0.5)',
                    transition: 'all 0.1s'
                }}
                onPointerDown={handlePointerDown}
                onPointerEnter={handlePointerEnter}
                onPointerLeave={handlePointerLeave}
            >
                <span style={{ color: currentTextColor, fontSize: '12px', fontWeight: val ? 'bold' : 'normal', textAlign: 'center', pointerEvents: 'none' }}>
                    {currentText}
                </span>
            </div>
        </div>
    );
};

window.ButtonToggle = ButtonToggle;
