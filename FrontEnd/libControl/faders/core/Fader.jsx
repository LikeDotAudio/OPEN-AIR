/**
 * Header: Fader.jsx
 * Purpose: Fader component or utility.
 * Description: Handles logic and rendering for Fader component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

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

// Inline comment: Logic for Fader
const Fader = ({ value: externalValue, onChange, config, topic, nodeJson }) => {
    // 1. Domain configuration
    const domainCfg = config?.domain?.primary || {};
    const min = domainCfg.min !== undefined ? domainCfg.min : (config?.value_min !== undefined ? config.value_min : -100.0);
    const max = domainCfg.max !== undefined ? domainCfg.max : (config?.value_max !== undefined ? config.value_max : 0.0);
    const logExponent = domainCfg.log_exponent !== undefined ? domainCfg.log_exponent : (config?.log_exponent !== undefined ? config.log_exponent : 1.0);
    // reff_point lives under interaction.* (nested) or flat (legacy).
    const reffPoint = config?.interaction?.reff_point ?? config?.reff_point ?? (min + max) / 2.0;

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

    // 3. Layout configuration. Fluid faders measure their rendered box and use
    //    that pixel width for geometry, so they REDRAW to fit (crisp) rather
    //    than being scaled/zoomed. Non-fluid faders keep their fixed geometry.
    // Orientation is authoritative from style.orientation OR the type name
    // (e.g. "_CustomHorizontalFader" / "_GuiFaderHorizontal"); only when neither
    // says so do we infer from the box aspect. Resolve it BEFORE picking default
    // geometry so a horizontal fader with no explicit size gets a WIDE default
    // (else it'd default to 100x250 and render as a stubby vertical-ish bar).
    const _typeStr = (config?.type || '').toLowerCase();
    const _explicitOrient = config?.style?.orientation
        || (_typeStr.includes('horizontal') ? 'horizontal'
            : _typeStr.includes('vertical') ? 'vertical' : null);
    const _hasExplicitW = (config?.geometry?.width ?? config?.layout?.width) != null;
    // Horizontal faders with no explicit width fluid-fill their cell (so a grid of
    // them fits cleanly) rather than overflowing at a fixed default width.
    const fluid = !!config?.fluid || (_explicitOrient === 'horizontal' && !_hasExplicitW);
    const [measured, setMeasured] = React.useState(null);
    const _cfgW = config?.geometry?.width ?? config?.layout?.width ?? (_explicitOrient === 'horizontal' ? 250 : 100);
    const _cfgH = config?.geometry?.height ?? config?.layout?.height ?? (_explicitOrient === 'horizontal' ? 80 : 250);
    const width = (fluid && measured && measured.w) ? measured.w : (typeof _cfgW === 'number' ? _cfgW : 100);
    const height = (typeof _cfgH === 'number' ? _cfgH : 250);
    const orientation = _explicitOrient || (width > height ? 'horizontal' : 'vertical');

    const topRes = 25;
    const botRes = 30;
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
    const [isDragging, setIsDragging] = React.useState(false);
    const [isHovered, setIsHovered] = React.useState(false);
    const containerRef = React.useRef(null);

    // Measure the rendered width for fluid faders so geometry follows the box.
    React.useEffect(() => {
        if (!fluid || !containerRef.current || typeof ResizeObserver === 'undefined') return;
        const ro = new ResizeObserver((entries) => {
            const w = Math.round(entries[0].contentRect.width);
            if (w > 0) setMeasured((m) => (m && m.w === w ? m : { w }));
        });
        ro.observe(containerRef.current);
        return () => ro.disconnect();
    }, [fluid]);

    const handleInteraction = (e) => {
        if (!containerRef.current) return;
        const rect = containerRef.current.getBoundingClientRect();
        
        // CSS transform scale factors: getBoundingClientRect gives scaled screen coords,
        // offsetHeight/Width give unscaled DOM coords. We divide the screen delta by
        // the scale to map the mouse back into the unscaled coordinate space.
        const scaleY = rect.height / (containerRef.current.offsetHeight || 1);
        const scaleX = rect.width / (containerRef.current.offsetWidth || 1);

        let norm = 0;
        if (orientation === 'vertical') {
            const y = (e.clientY - rect.top) / scaleY;
            norm = 1 - (y - topRes - padding) / travelHeight;
        } else {
            const x = (e.clientX - rect.left) / scaleX;
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
    // Scale config (cosmetics.scale.*): show gate, major interval, sub-tick count,
    // tick size/thickness. "show ticks" now actually gates rendering.
    const scaleCfg = config?.cosmetics?.scale || {};
    const showTicks = scaleCfg.show !== undefined ? scaleCfg.show
        : (config?.show_ticks !== undefined ? config.show_ticks : true);
    
    // Core Colors. Sub-config keys now nest under cosmetics.colors.* (canonical,
    // matching the _SmartFader reference); flat keys kept as legacy fallbacks.
    const capColor = cosm.cap || config?.cap_color || '#dcdcdc';
    const highlightColor = cosm.cap_highlight || cosm.cap_highlights || config?.cap_highlight_color || null;
    
    // Fader Base colors matching Python theme defaults
    const bgCol = cosm.bg || config?.bg_color || 'transparent'; // Outer background
    const trackCol = cosm.primary || config?.fader_track_color || config?.track_col || '#050505';
    const trackHoverCol = cosm.track_hover || config?.track_hover_color || '#444444';
    const valHighlightCol = cosm.highlight || config?.value_highlight_color || config?.value_highlight || '#f4902c';
    
    // Borders
    const borderWidth = config?.border_width || 0;
    const borderColor = config?.border_color || 'black';

    // Ticks Colors (nested cosmetics.colors.* first, then flat, then secondary).
    const tickCol = cosm.tick_color || config?.tick_color || cosm.secondary || 'lightgrey';
    const tickTextCol = config?.tick_text_color || tickCol;
    const subTickCol = cosm.sub_tick_color || config?.sub_tick_color || tickCol;
    const subTickTextCol = config?.sub_tick_text_color || subTickCol;

    // Display Preferences (readout.* nested first, then flat legacy keys).
    const showValue = config?.readout?.show_value !== false && config?.readout?.show !== false && config?.show_value !== false;
    const showUnits = config?.readout?.show_units ?? config?.show_units ?? false;
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
                width: fluid ? '100%' : width, height,
                position: 'relative',
                backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, bgCol) : bgCol),
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

            {/* Scale / Ticks — gated by show ticks (cosmetics.scale.show) */}
            {showTicks && (
            <FaderScale
                min={min} max={max} logExponent={logExponent}
                width={width} height={height - botRes}
                availableLength={orientation === 'vertical' ? travelHeight : travelWidth}
                paddingStart={topRes + padding}
                tickSize={scaleCfg.size ?? config?.tick_size ?? config?.style?.tick_size ?? 0.35}
                slotSize={trackSlotWidth}
                capWidth={capW} // capW represents the width across the track, regardless of rotation
                tickColor={tickCol}
                subTickColor={subTickCol}
                tickTextColor={tickTextCol}
                subTickTextColor={subTickTextCol}
                tickThickness={scaleCfg.thickness ?? config?.tick_thickness ?? config?.style?.tick_thickness ?? 1}
                customTicks={styleOverrides.custom_ticks || config?.custom_ticks || config?.ticks || null}
                interval={scaleCfg.interval ?? config?.tick_interval ?? null}
                subTicks={scaleCfg.sub_ticks ?? config?.sub_ticks ?? 4}
                style={scaleCfg.style ?? config?.tick_style ?? 'simple'}
                sides={scaleCfg.sides ?? scaleCfg.side ?? null}
                orientation={orientation}
            />
            )}

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
                    position: 'absolute', bottom: 5, left: 0, width: '100%',
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

window.Fader = Fader;