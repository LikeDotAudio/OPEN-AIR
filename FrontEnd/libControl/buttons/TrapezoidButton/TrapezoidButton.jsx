/**
 * Header: TrapezoidButton.jsx
 * Purpose: TrapezoidButton component or utility.
 * Description: Handles logic and rendering for TrapezoidButton component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

/**
 * OcaTrapezoidButton Component
 * Author: Anthony Peter Kuzub / Gemini (Collaborator)
 * Version: 20260506.2100.1
 *
 * Description: High-fidelity 3D Trapezoidal button with state-dependent lighting.
 * Based on the industrial standard at oaGuiElements/Core/buttons/button_trapezoid
 */

// Inline comment: Logic for OcaTrapezoidButton
const OcaTrapezoidButton = ({ label: externalLabel, value, onChange, config }) => {
    const [isPressed, setIsPressed] = React.useState(false);
    const [lang] = window.useMqttLang ? window.useMqttLang() : ['En'];

    // --- 1. Robust Config & Geometry Extraction ---
    const c = config || {};
    const cosmetics = c.cosmetics || {};
    const colors = cosmetics.colors || {};
    const styling = cosmetics.styling || {};
    
    // Industrial Scaling Factors (from Python)
    const WIDTH_SCALING_FACTOR = 0.8;
    const HEIGHT_SCALING_FACTOR = 0.8;
    const PRESSED_OFFSET_Y = 4;
    const BEVEL_WIDTH_RATIO = 0.15;
    const TOP_SHRINK_RATIO = 0.1;
    const INDICATOR_WIDTH_RATIO = 0.4;
    const INDICATOR_HEIGHT_RATIO = 0.15;
    const INDICATOR_Y_RATIO = 0.75; // Lower placement

    const canvasW = c.geometry?.width || c.width || 100;
    const canvasH = (c.geometry?.height || c.height || 60);
    
    const buttonW = canvasW * WIDTH_SCALING_FACTOR;
    const buttonH = (c.geometry?.height || c.height || 50) * HEIGHT_SCALING_FACTOR;
    
    const latching = c.latching === true;
    const isLit = value === 1 || value === true || (typeof value === 'string' && (value.toLowerCase() === 'on' || value === '1'));

    // THE BODY CARRIES THE STATE, NOT JUST THE LAMP.
    //
    // The face colour was a constant and only the indicator rectangle moved, so
    // "is the output live?" was a question about a 40x9 px strip. On a signal
    // generator that answer has to be readable from across the bench: red face
    // means RF is on the connector, white face means it is not.
    //
    // `color_active` / `color_inactive` colour the face per state. Either one
    // absent falls back to the single `color` every existing trapezoid already
    // sets, so nothing authored before this changes appearance.
    const baseColor = (isLit ? c.color_active : c.color_inactive)
        || c.color || styling.fill_color || colors.primary || '#8B0000';
    const ledColor = c.led_color || colors.active || '#FF0000';
    // Wording may differ per state (ON / OFF) — the same label:{active,inactive}
    // pair every other button reads, expanded to label_active/label_inactive by
    // FieldComponent. A node with only `active` keeps its one caption.
    const stateText = (l) => (typeof l === 'string' ? l : (l?.[lang] || l?.En || ""));
    const buttonText = c.button_text || stateText(
        (isLit || c.label_inactive === undefined) ? c.label_active : c.label_inactive
    );
    const labelText = externalLabel || c.label?.[lang] || c.label?.En || "";

    // --- 2. Color Lightness Engine (The Gold) ---
    const adjustColor = (hex, factor) => {
        hex = hex.replace('#', '');
        if (hex.length === 3) hex = hex.split('').map(s => s + s).join('');
        try {
            const r = Math.max(0, Math.min(255, Math.floor(parseInt(hex.substring(0, 2), 16) * factor)));
            const g = Math.max(0, Math.min(255, Math.floor(parseInt(hex.substring(2, 4), 16) * factor)));
            const b = Math.max(0, Math.min(255, Math.floor(parseInt(hex.substring(4, 6), 16) * factor)));
            return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
        } catch (e) { return '#8B0000'; }
    };

    const faceColor = adjustColor(baseColor, isPressed ? 0.8 : 1.0);
    const topBevel = adjustColor(baseColor, isPressed ? 0.9 : 1.2);
    const bottomBevel = adjustColor(baseColor, 0.5);
    const sideBevel = adjustColor(baseColor, 0.7);
    const indColor = isLit ? ledColor : adjustColor(baseColor, 0.3);

    // The caption was painted white unconditionally, which was safe only while
    // every trapezoid was dark. A white OFF face made its own label vanish. Pick
    // by the face's luminance instead, still overridable per state.
    const luminance = (hex) => {
        let h = String(hex).replace('#', '');
        if (h.length === 3) h = h.split('').map(s => s + s).join('');
        const v = parseInt(h, 16);
        if (Number.isNaN(v) || h.length !== 6) return 0;
        // Rec. 709 weights: green reads far brighter to the eye than blue.
        return (0.2126 * ((v >> 16) & 255) + 0.7152 * ((v >> 8) & 255) + 0.0722 * (v & 255)) / 255;
    };
    const textColor = (isLit ? c.text_color_active : c.text_color_inactive)
        || c.text_color || (luminance(faceColor) > 0.6 ? '#111111' : '#ffffff');

    // --- 3. Interaction Handlers ---
    const handlePointerDown = (e) => {
        setIsPressed(true);
        e.target.setPointerCapture(e.pointerId);
    };

    const handlePointerUp = (e) => {
        if (!isPressed) return;
        setIsPressed(false);
        e.target.releasePointerCapture(e.pointerId);
        
        const nextVal = latching ? (isLit ? 0 : 1) : (isLit ? 0 : 1); 
        // Note: For momentary, the caller usually handles the reset, 
        // but we send the 'toggle' event.
        onChange(nextVal);
    };

    // --- 4. Geometry Math ---
    const centerX = canvasW / 2;
    const centerY = (canvasH + (labelText ? 15 : 0)) / 2;
    const base_x = centerX - buttonW / 2;
    const base_y = centerY - buttonH / 2;
    
    const offsetY = isPressed ? PRESSED_OFFSET_Y : 0;
    const bevelW = buttonW * BEVEL_WIDTH_RATIO;
    const topShrink = c.slant !== undefined ? c.slant : (buttonW * TOP_SHRINK_RATIO);

    const ptOuter = [
        base_x, base_y + buttonH + offsetY,
        base_x + topShrink, base_y + offsetY,
        base_x + buttonW - topShrink, base_y + offsetY,
        base_x + buttonW, base_y + buttonH + offsetY
    ];
    
    const ptInner = [
        base_x + bevelW, base_y + buttonH - bevelW + offsetY,
        base_x + topShrink + bevelW * 0.5, base_y + bevelW + offsetY,
        base_x + buttonW - topShrink - bevelW * 0.5, base_y + bevelW + offsetY,
        base_x + buttonW - bevelW, base_y + buttonH - bevelW + offsetY
    ];

    const toStr = (pts) => {
        let s = "";
        for(let i=0; i<pts.length; i+=2) s += `${pts[i]},${pts[i+1]} `;
        return s.trim();
    };

    const filterId = `glow-trap-${c.id || Math.random().toString(36).substr(2, 9)}`;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', userSelect: 'none' }}>
            {labelText && (
                <div style={{ fontSize: '9px', color: '#888', marginBottom: '2px', fontWeight: 'bold' }}>
                    {labelText.toUpperCase()}
                </div>
            )}
            
            <svg 
                width={canvasW} 
                height={canvasH + 10} 
                style={{ touchAction: 'none', cursor: 'pointer', overflow: 'visible' }}
                onPointerDown={handlePointerDown}
                onPointerUp={handlePointerUp}
                onPointerCancel={() => setIsPressed(false)}
            >
                <defs>
                    <filter id={filterId} x="-50%" y="-50%" width="200%" height="200%">
                        <feGaussianBlur stdDeviation="4" result="blur" />
                        <feComposite in="SourceGraphic" in2="blur" operator="over"/>
                    </filter>
                </defs>

                {/* 1. Industrial Shadow (only when not pressed) */}
                {!isPressed && (
                    <polygon points={toStr([
                        base_x - 2, base_y + buttonH + 6,
                        base_x + topShrink - 2, base_y + 6,
                        base_x + buttonW - topShrink + 2, base_y + 6,
                        base_x + buttonW + 2, base_y + buttonH + 6
                    ])} fill="#111" />
                )}

                {/* 2. Bezel/Body Construction */}
                <polygon points={toStr(ptOuter)} fill={faceColor} stroke="#222" strokeWidth="1" />
                
                {/* 3. High-Fidelity Bevels */}
                <polygon points={toStr([ptOuter[0], ptOuter[1], ptInner[0], ptInner[1], ptInner[6], ptInner[7], ptOuter[6], ptOuter[7]])} fill={bottomBevel} />
                <polygon points={toStr([ptOuter[2], ptOuter[3], ptInner[2], ptInner[3], ptInner[4], ptInner[5], ptOuter[4], ptOuter[5]])} fill={topBevel} />
                <polygon points={toStr([ptOuter[0], ptOuter[1], ptInner[0], ptInner[1], ptInner[2], ptInner[3], ptOuter[2], ptOuter[3]])} fill={sideBevel} />
                <polygon points={toStr([ptOuter[6], ptOuter[7], ptInner[6], ptInner[7], ptInner[4], ptInner[5], ptOuter[4], ptOuter[5]])} fill={sideBevel} />

                {/* 4. Top Face */}
                <polygon points={toStr(ptInner)} fill={faceColor} />

                {/* 5. LED Indicator */}
                <rect 
                    x={centerX - (buttonW * INDICATOR_WIDTH_RATIO)/2} 
                    y={base_y + buttonH * INDICATOR_Y_RATIO + offsetY} 
                    width={buttonW * INDICATOR_WIDTH_RATIO} 
                    height={buttonH * INDICATOR_HEIGHT_RATIO} 
                    fill={indColor} 
                    stroke="#111" 
                    filter={isLit ? `url(#${filterId})` : ''}
                />

                {/* 6. Button Text */}
                {buttonText && (
                    <text 
                        x={centerX} 
                        y={base_y + buttonH * 0.6 + offsetY}
                        fill={textColor}
                        fontSize={c.text_size || 9}
                        fontWeight="bold" 
                        fontFamily="Arial, sans-serif" 
                        textAnchor="middle"
                        dominantBaseline="middle"
                        pointerEvents="none"
                    >
                        {buttonText.toUpperCase()}
                    </text>
                )}
            </svg>
        </div>
    );
};

window.OcaTrapezoidButton = OcaTrapezoidButton;