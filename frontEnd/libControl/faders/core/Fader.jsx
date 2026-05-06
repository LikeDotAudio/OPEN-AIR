// Fader Component (OrchestrAator)
// Author: Gemini (Collaborator)
// Version: 20260506.1400.4
//
// Description: High-fidelity React Fader component matching Python render geometry, 
// including interaction details (wheel, alt-click, double-click) and advanced config support.



const FaderCap = window.FaderCap;
const FaderScale = window.FaderScale;
const clamp = window.FaderUtils.clamp;
const mapValueToPosition = window.FaderUtils.mapValueToPosition;
const mapPositionToValue = window.FaderUtils.mapPositionToValue;

const Fader = ({ value: externalValue, onChange, config, topic, nodeJson }) => {
    // 1. Domain configuration
    const domainCfg = config?.domain?.primary || {};
    const min = domainCfg.min !== undefined ? domainCfg.min : (config?.value_min !== undefined ? config.value_min : -100.0);
    const max = domainCfg.max !== undefined ? domainCfg.max : (config?.value_max !== undefined ? config.value_max : 0.0);
    const logExponent = domainCfg.log_exponent !== undefined ? domainCfg.log_exponent : (config?.log_exponent !== undefined ? config.log_exponent : 1.0);
    const reffPoint = config?.reff_point !== undefined ? config.reff_point : (min + max) / 2.0;

    // 2. MQTT integration
    const useMqtt = !!topic;
    const useMqttState = window.useMqttState;
    const [val, setVal] = useMqtt ? useMqttState(topic, externalValue || min, nodeJson) : [externalValue, onChange, 'En'];
    const currentValue = useMqtt ? val : (externalValue !== undefined ? externalValue : min);

    const setCurrentValue = (newVal) => {
        const clampedVal = clamp(newVal, min, max);
        if (useMqtt) {
            setVal(clampedVal);
        } else if (onChange) {
            onChange(clampedVal);
        }
    };

    // 3. Layout configuration
    const width = config?.geometry?.width || config?.layout?.width || 100;
    const height = config?.geometry?.height || config?.layout?.height || 250;
    const orientation = config?.style?.orientation || (width > height ? 'horizontal' : 'vertical');

    const topRes = 25;
    const botRes = 20;
    const faderCapScale = config?.geometry?.fader_cap_scale ?? config?.fader_cap_scale ?? 1.0;
    const capW = (config?.geometry?.cap?.x || config?.cap_width || 40) * faderCapScale;
    const capH = (config?.geometry?.cap?.y || config?.cap_height || 50) * faderCapScale;
    const padding = capH / 2;
    const trackSlotWidth = 10;

    const travelHeight = height - topRes - botRes - (2 * padding);
    const travelWidth = width - topRes - botRes - (2 * padding);

    // 4. Position Calculation
    const displayNorm = mapValueToPosition(currentValue, min, max, logExponent);
    const capPos = orientation === 'vertical' 
        ? travelHeight * (1 - displayNorm) + topRes + padding
        : travelWidth * displayNorm + topRes + padding;

    // 5. Interaction State
    const [isDragging, setIsDragging] = useState(false);
    const [isHovered, setIsHovered] = useState(false);
    const containerRef = useRef(null);

    const handleInteraction = (e) => {
        if (!containerRef.current) return;
        const rect = containerRef.current.getBoundingClientRect();
        let norm = 0;
        if (orientation === 'vertical') {
            const y = e.clientY - rect.top;
            norm = 1 - (y - topRes - padding) / travelHeight;
        } else {
            const x = e.clientX - rect.left;
            norm = (x - topRes - padding) / travelWidth;
        }
        setCurrentValue(mapPositionToValue(norm, min, max, logExponent));
    };

    const onPointerDown = (e) => {
        setIsDragging(true);
        handleInteraction(e);
        e.currentTarget.setPointerCapture(e.pointerId);
    };

    const onPointerMove = (e) => {
        if (isDragging) handleInteraction(e);
    };

    const onPointerUp = (e) => {
        setIsDragging(false);
        e.currentTarget.releasePointerCapture(e.pointerId);
    };

    const onWheel = (e) => {
        e.preventDefault();
        const step = (max - min) * 0.05;
        const delta = Math.sign(e.deltaY) * -1; // Standard scroll down = negative Y = decrease
        setCurrentValue(currentValue + (delta * step));
    };

    const onDoubleClick = (e) => {
        e.preventDefault();
        setCurrentValue(reffPoint);
    };

    const onClick = (e) => {
        if (e.altKey) {
            const input = prompt("Manual Value Entry:", currentValue);
            if (input !== null) {
                const parsed = parseFloat(input);
                if (!isNaN(parsed)) setCurrentValue(parsed);
            }
        }
    };

    // 6. Cosmetics & Style Mapping
    const cosm = config?.cosmetics?.colors || {};
    const styleOverrides = config?.cosmetics?.style_overrides || {};
    
    // Core Colors
    const capColor = cosm.cap || config?.cap_color || '#dcdcdc';
    const highlightColor = cosm.cap_highlights || config?.cap_highlight_color || null;
    
    // Fader Base colors matching Python theme defaults
    const bgCol = cosm.bg || config?.bg_color || 'transparent'; // Outer background
    const trackCol = cosm.primary || config?.fader_track_color || config?.track_col || '#050505';
    const trackHoverCol = cosm.track_hover || config?.track_hover_color || '#444444';
    const valHighlightCol = cosm.highlight || config?.value_highlight_color || config?.value_highlight || '#f4902c';
    
    // Borders
    const borderWidth = config?.border_width || 0;
    const borderColor = config?.border_color || 'black';

    // Ticks Colors
    const tickCol = config?.tick_color || cosm.secondary || 'lightgrey';
    const tickTextCol = config?.tick_text_color || tickCol;
    const subTickCol = config?.sub_tick_color || tickCol;
    const subTickTextCol = config?.sub_tick_text_color || subTickCol;

    // Display Preferences
    const showValue = config?.readout?.show !== false && config?.show_value !== false;
    const showUnits = config?.show_units ?? false;
    const unitText = config?.unit_text ?? "";
    const unitPosition = config?.unit_position ?? "right";
    const movementDisplay = config?.movement_value_display ?? true;
    
    const formattedVal = currentValue === Math.floor(currentValue) ? currentValue.toString() : currentValue.toFixed(1);
    const readOutStr = showUnits && unitText 
        ? (unitPosition === 'right' ? `${formattedVal} ${unitText}` : `${unitText} ${formattedVal}`)
        : formattedVal;

    // Track Geometry (Matching TrackDrawer recessed box)
    const trackX = orientation === 'vertical' ? width/2 - trackSlotWidth/2 : topRes + padding - 5;
    const trackY = orientation === 'vertical' ? topRes + padding - 5 : height/2 - trackSlotWidth/2;
    const trackW = orientation === 'vertical' ? trackSlotWidth : travelWidth + 10;
    const trackH = orientation === 'vertical' ? travelHeight + 10 : trackSlotWidth;

    const labelText = config?.label?.En || config?.label?.text || (typeof config?.label === 'string' ? config.label : '');

    return (
        <div 
            ref={containerRef} 
            className={`fader-container ${orientation}`} 
            style={{ 
                width, height, 
                position: 'relative', 
                backgroundColor: bgCol,
                touchAction: 'none',
                overflow: 'hidden',
                border: borderWidth ? `${borderWidth}px solid ${borderColor}` : 'none',
                boxSizing: 'border-box'
            }}
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onPointerEnter={() => setIsHovered(true)}
            onPointerLeave={() => setIsHovered(false)}
            onWheel={onWheel}
            onDoubleClick={onDoubleClick}
            onClick={onClick}
        >
            {/* Label */}
            {labelText && (
                <div style={{
                    position: 'absolute', top: 12, left: 0, width: '100%',
                    textAlign: 'center', color: config?.label_color || 'white',
                    fontSize: 10, fontWeight: 'bold', pointerEvents: 'none',
                    zIndex: 2
                }}>
                    {labelText}
                </div>
            )}

            {/* Scale / Ticks */}
            <FaderScale 
                min={min} max={max} logExponent={logExponent}
                width={width} height={height - botRes}
                availableLength={orientation === 'vertical' ? travelHeight : travelWidth}
                paddingStart={topRes + padding}
                tickSize={config?.tick_size ?? config?.style?.tick_size ?? 0.35}
                slotSize={trackSlotWidth}
                capWidth={capW} // capW represents the width across the track, regardless of rotation
                tickColor={tickCol}
                subTickColor={subTickCol}
                tickTextColor={tickTextCol}
                subTickTextColor={subTickTextCol}
                tickThickness={config?.tick_thickness ?? config?.style?.tick_thickness ?? 1}
                tickLabelPosition={config?.tick_label_position ?? config?.style?.tick_label_position ?? 'right'}
                customTicks={styleOverrides.custom_ticks || config?.custom_ticks || null}
                orientation={orientation}
            />

            {/* 3D Recessed Track Slot */}
            <div style={{
                position: 'absolute',
                left: trackX,
                top: trackY,
                width: trackW,
                height: trackH,
                backgroundColor: isHovered ? trackHoverCol : trackCol,
                border: '1px solid #222',
                boxShadow: 'inset 1px 1px 3px #000, inset -1px -1px 2px #333',
                pointerEvents: 'none',
                boxSizing: 'border-box',
                zIndex: 1
            }} />

            {/* Fader Cap Wrapper - Dimensions match the cap bounds so translate(-50%, -50%) centers perfectly */}
            <div style={{
                position: 'absolute',
                left: orientation === 'vertical' ? width/2 : capPos,
                top: orientation === 'vertical' ? capPos : height/2,
                width: orientation === 'vertical' ? capW : capH,
                height: orientation === 'vertical' ? capH : capW,
                transform: 'translate(-50%, -50%)',
                pointerEvents: 'none',
                zIndex: 3
            }}>
                <FaderCap 
                    width={capW} 
                    height={capH}
                    capColor={capColor}
                    highlightColor={highlightColor}
                    orientation={orientation}
                />
            </div>

            {/* Floating Value (only when dragging, if enabled) */}
            {isDragging && movementDisplay && (
                <div style={{
                    position: 'absolute',
                    left: orientation === 'vertical' ? width/2 : capPos,
                    top: orientation === 'vertical' ? capPos - 25 : height/2 - 35,
                    transform: 'translateX(-50%)',
                    color: 'white', fontSize: 10, fontWeight: 'bold',
                    pointerEvents: 'none',
                    textShadow: '0px 0px 3px black',
                    zIndex: 10
                }}>
                    {readOutStr}
                </div>
            )}

            {/* Static Readout */}
            {showValue && (
                <div style={{
                    position: 'absolute', bottom: 10, left: 0, width: '100%',
                    textAlign: 'center', color: valHighlightCol,
                    fontSize: 10, pointerEvents: 'none',
                    zIndex: 2
                }}>
                    {readOutStr}
                </div>
            )}
        </div>
    );
};

window.Fader = Fader;      </div>
            )}
        </div>
    );
};

window.Fader = Fader;