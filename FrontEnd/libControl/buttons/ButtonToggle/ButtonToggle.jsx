/**
 * Header: ButtonToggle.jsx
 * Purpose: ButtonToggle component or utility.
 * Description: Handles logic and rendering for ButtonToggle component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// ButtonToggle Component
// Author: Gemini (Collaborator)
// Version: 20260507.1000.1
//
// Description: Stateful toggle button component matching Python's ToggleButton.

// Inline comment: Logic for ButtonToggle
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
    
    // Style schema: style.active / style.inactive parents (same params each),
    // falling back to legacy flat keys under `style` (this is what makes
    // active_text_color etc. actually render — they were read off config before).
    const styleObj = config?.style || {};
    const A = styleObj.active || {};
    const I = styleObj.inactive || {};
    const pk = (...vals) => vals.find((v) => v !== undefined && v !== null);
    const grpActive = {
        text_color: pk(A.text_color, styleObj.active_text_color, '#1a1a1a'),
        bg_color: pk(A.bg_color, styleObj.active_bg_color, '#000000'),
        border_color: pk(A.border_color, styleObj.active_color, '#FF9900'),
        border_thickness: pk(A.border_thickness, 2),
        glow_intensity: pk(A.glow_intensity, styleObj.glow_intensity, 10),
        font_style: pk(A.font_style, styleObj.active_font_style, 'bold'),
        font_size: pk(A.font_size, styleObj.active_font_size),
    };
    const grpInactive = {
        text_color: pk(I.text_color, styleObj.text_color, '#888888'),
        bg_color: pk(I.bg_color, styleObj.bg_color, '#1a1a1a'),
        border_color: pk(I.border_color, '#555'),
        border_thickness: pk(I.border_thickness, 2),
        glow_intensity: pk(I.glow_intensity, 0),
        font_style: pk(I.font_style, styleObj.inactive_font_style, 'normal'),
        font_size: pk(I.font_size, styleObj.inactive_font_size),
    };

    const isHovered = React.useRef(false);
    const [hoverState, setHoverState] = React.useState(false);

    const s = val ? grpActive : grpInactive;
    const currentText = val ? onText : offText;
    const currentBg = s.bg_color;
    const currentBorder = s.border_color;
    const currentTextColor = s.text_color;
    const borderW = s.border_thickness || 2;
    const glow = s.glow_intensity || 0;
    const fontWeight = s.font_style === 'bold' ? 'bold' : 'normal';
    const fontStyleCss = s.font_style === 'italic' ? 'italic' : 'normal';
    const fontSizeCss = s.font_size ? `${s.font_size}px` : '12px';

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
                    backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, currentBg) : currentBg),
                    border: `${borderW}px solid ${isHovered.current ? (val ? grpActive.border_color : '#888') : currentBorder}`,
                    borderRadius: `${cornerRadius}px`,
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    cursor: 'pointer',
                    userSelect: 'none',
                    boxShadow: glow > 0 ? `inset 0 0 ${Math.min(40, glow * 3)}px ${currentBorder}` : (val ? 'none' : 'inset 0 0 5px rgba(0,0,0,0.5)'),
                    transition: 'all 0.1s'
                }}
                onPointerDown={handlePointerDown}
                onPointerEnter={handlePointerEnter}
                onPointerLeave={handlePointerLeave}
            >
                <span style={{ color: currentTextColor, fontSize: fontSizeCss, fontWeight, fontStyle: fontStyleCss, textAlign: 'center', pointerEvents: 'none' }}>
                    {currentText}
                </span>
            </div>
        </div>
    );
};

window.ButtonToggle = ButtonToggle;
