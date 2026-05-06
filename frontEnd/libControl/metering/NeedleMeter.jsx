function useNeedleBallistics(rawValueRef, canvasRef, min, max, width, height, config) {
    React.useEffect(() => {
        let displayValue = min;
        let animationFrameId;

        const render = () => {
            const raw = rawValueRef.current;
            
            // Analog Ballistics Logic (usually fast attack, medium release for VU)
            const attack = config?.dynamics?.attack_ms ? (100 / config.dynamics.attack_ms) * 0.5 : 0.3;
            const release = config?.dynamics?.release_ms ? (100 / config.dynamics.release_ms) * 0.5 : 0.1;

            if (raw > displayValue) {
                displayValue += (raw - displayValue) * attack; 
            } else {
                displayValue -= (displayValue - raw) * release;
            }

            if (canvasRef.current) {
                const ctx = canvasRef.current.getContext('2d');
                ctx.clearRect(0, 0, width, height);

                const styleOv = config?.cosmetics?.style_overrides || {};
                const colors = config?.cosmetics?.colors || {};

                // --- Geometry & Cosmetics Math ---
                const centerX = width / 2 + (styleOv.pivot_offset_x || 0);
                const centerY = height / 2 + (styleOv.pivot_offset_y || 0); // Use centered Y based on height/width
                
                // Meter size based on smaller dimension for aspect ratio
                const meterSize = Math.min(width, height);
                const baseArcRadius = meterSize / 2 * (styleOv.arc_radius_factor || 0.85); // Default arc radius factor
                const arcRadius = styleOv.arc_radius_offset ? baseArcRadius + styleOv.arc_radius_offset : baseArcRadius;
                
                const centerAngleDeg = config?.Meter_center_angle || config?.meter_center_angle || 90; // 90 is straight up
                const viewableAngleDeg = config?.Meter_viewable_angle || config?.meter_viewable_angle || 90; // 90 degree sweep
                
                const startAngleDeg = centerAngleDeg + (viewableAngleDeg / 2);
                const endAngleDeg = centerAngleDeg - (viewableAngleDeg / 2);
                
                // Conversion to Canvas radians (0=right, positive=clockwise, math y-axis inverted)
                const toCanvasRad = (deg) => -deg * Math.PI / 180.0;
                const radStart = toCanvasRad(startAngleDeg);
                const radEnd = toCanvasRad(endAngleDeg);
                
                // Needle Angle Calculation
                const minVal = min;
                const maxVal = max;
                const range = (maxVal - minVal) || 1;
                const boundedVal = Math.max(minVal, Math.min(maxVal, displayValue));
                const normVal = (boundedVal - minVal) / range;
                const needleAngleDeg = startAngleDeg - (normVal * viewableAngleDeg);
                const needleAngleRad = toCanvasRad(needleAngleDeg);

                // Background Faceplate
                ctx.fillStyle = colors.background || config?.bg_color || '#2b2b2b';
                ctx.fillRect(0, 0, width, height);
                
                // Bezel Drawing based on style_overrides.bezel_shape
                const bezelShape = styleOv.bezel_shape || 'circle';
                const bezelWidth = styleOv.bezel_width || 5;
                const bezelColor = colors.bezel || '#111';
                const faceColor = styleOv.meter_face_colour === 'transparent' ? 'transparent' : (colors.meter_face_colour || colors.faceplate || '#111');
                
                // Shadow for bezel
                ctx.shadowColor = 'rgba(0,0,0,0.8)';
                ctx.shadowBlur = 10;
                ctx.shadowOffsetX = 2;
                ctx.shadowOffsetY = 2;

                ctx.fillStyle = bezelColor;
                ctx.beginPath();
                const R = arcRadius + bezelWidth; // Radius for bezel edge

                if (bezelShape === 'hotdog') {
                    const hW = width * 0.6; // Horizontal width for hotdog
                    const hH = arcRadius * 1.6; // Horizontal height for hotdog
                    const hX = centerX - hW / 2;
                    const hY = centerY - hH / 2;
                    ctx.roundRect(hX, hY, hW, hH, hH/2); // Rounded rectangle
                } else if (bezelShape === 'gem') {
                    const r = arcRadius + bezelWidth;
                    ctx.moveTo(centerX, centerY - r); // Top point
                    ctx.lineTo(centerX + r * Math.cos(toCanvasRad(30)), centerY + r * Math.sin(toCanvasRad(30))); // Bottom right
                    ctx.lineTo(centerX + r * Math.cos(toCanvasRad(150)), centerY + r * Math.sin(toCanvasRad(150))); // Top right
                    ctx.closePath();
                } else if (bezelShape === 'parking_meter') {
                    const r = arcRadius + bezelWidth;
                    ctx.arc(centerX, centerY, r, toCanvasRad(startAngle), toCanvasRad(endAngle), true); // Semi-circle base
                    ctx.lineTo(centerX, centerY); // Line back to center
                    ctx.closePath();
                } else if (bezelShape === 'squircle') {
                    const r = arcRadius + bezelWidth;
                    ctx.roundRect(centerX - r, centerY - r, r * 2, r * 2, 10);
                } else if (bezelShape === 'trapezoid') {
                    const r = arcRadius + bezelWidth;
                    const bottomW = r * 2;
                    const topW = r * 1.2;
                    ctx.moveTo(centerX - bottomW/2, centerY + r);
                    ctx.lineTo(centerX - topW/2, centerY - r);
                    ctx.lineTo(centerX + topW/2, centerY - r);
                    ctx.lineTo(centerX + bottomW/2, centerY + r);
                    ctx.closePath();
                } else if (bezelShape === 'hex') {
                    const r = arcRadius + bezelWidth;
                    const pts = [];
                    for (let i = 0; i < 6; i++) {
                        const a = (i / 6) * Math.PI * 2 + (Math.PI / 6);
                        pts.push(`${centerX + r * Math.cos(a)},${centerY + r * Math.sin(a)}`);
                    }
                    ctx.beginPath();
                    ctx.moveTo(pts[0].split(',')[0], pts[0].split(',')[1]);
                    for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].split(',')[0], pts[i].split(',')[1]);
                    ctx.closePath();
                } else { // Default to circle
                    ctx.arc(centerX, centerY, arcRadius + bezelWidth, 0, Math.PI * 2);
                }
                ctx.fill();
                ctx.shadowColor = 'transparent';

                // Faceplate rendering (masked or transparent)
                if (faceColor !== 'transparent') {
                    ctx.fillStyle = faceColor;
                    ctx.beginPath();
                    ctx.arc(centerX, centerY, arcRadius, radStart, radEnd, true); // Use meter's arc for faceplate
                    ctx.fill();
                }

                // Scale Arcs
                ctx.lineWidth = config?.curve_thickness || 3;
                
                // Red Zone math
                const upperRange = styleOv.upper_range !== undefined ? styleOv.upper_range : (config?.upper_range || 0.0);
                const normUpper = (upperRange - minVal) / range;
                const upperAngle = startAngle - (normUpper * viewableAngleDeg);
                const upperRad = toCanvasRad(upperAngle);
                
                const primColor = colors.primary || '#E0E0E0';
                const alertColor = colors.alert || '#CC3333';

                // Main Arc
                ctx.beginPath();
                ctx.arc(centerX, centerY, arcRadius, radStart, upperRad, true);
                ctx.strokeStyle = primColor;
                ctx.stroke();

                // Alert Arc
                if (upperRange < maxVal) {
                    ctx.beginPath();
                    ctx.arc(centerX, centerY, arcRadius, radEnd, upperRad, true);
                    ctx.strokeStyle = alertColor;
                    ctx.stroke();
                }

                // Ticks & Text
                const tickLen = styleOv.tick_length || 8;
                const subTickLen = styleOv.sub_tick_length || 4;
                ctx.fillStyle = colors.text || primColor;
                ctx.strokeStyle = colors.text || primColor;
                ctx.lineWidth = 1.5;
                ctx.font = 'bold 9px Arial';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';

                const step = config?.domain?.primary?.step || 5.0;
                const tickSteps = Math.abs(range / step);
                const subTicks = styleOv.sub_ticks || config?.sub_ticks || 0;
                const subTickStyle = styleOv.sub_tick_style || 'line';
                
                for(let i=0; i<=tickSteps; i++) {
                    const val = minVal + (i * step);
                    const tNorm = (val - minVal) / range;
                    const tDeg = startAngle - (tNorm * viewableAngleDeg);
                    const tRad = toCanvasRad(tDeg);
                    
                    const isAlert = val >= upperRange;
                    ctx.strokeStyle = isAlert ? alertColor : primColor;
                    ctx.fillStyle = isAlert ? alertColor : primColor;

                    const x1 = centerX + arcRadius * Math.cos(tRad);
                    const y1 = centerY + arcRadius * Math.sin(tRad);
                    const x2 = centerX + (arcRadius - tickLen) * Math.cos(tRad);
                    const y2 = centerY + (arcRadius - tickLen) * Math.sin(tRad);
                    
                    ctx.beginPath();
                    ctx.moveTo(x1, y1);
                    ctx.lineTo(x2, y2);
                    ctx.stroke();

                    // Label
                    const tx = centerX + (arcRadius - tickLen - 12) * Math.cos(tRad);
                    const ty = centerY + (arcRadius - tickLen - 12) * Math.sin(tRad);
                    ctx.fillText(Math.round(val), tx, ty);

                    // Subticks
                    if (i < tickSteps && subTicks > 0) {
                        for(let j=1; j<=subTicks; j++) {
                            const subNorm = tNorm + (1/tickSteps) * (j / (subTicks + 1));
                            const subDeg = startAngle - (subNorm * viewableAngleDeg);
                            const subRad = toCanvasRad(subDeg);
                            
                            const valSub = minVal + (subNorm * range);
                            const isAlertSub = valSub >= upperRange;
                            ctx.strokeStyle = isAlertSub ? alertColor : primColor;
                            ctx.fillStyle = isAlertSub ? alertColor : primColor;

                            const sx1 = centerX + arcRadius * Math.cos(subRad);
                            const sy1 = centerY + arcRadius * Math.sin(subRad);
                            const sx2 = centerX + (arcRadius - subTickLen) * Math.cos(subRad);
                            const sy2 = centerY + (arcRadius - subTickLen) * Math.sin(subRad);

                            if (subTickStyle === 'dot') {
                                ctx.beginPath();
                                ctx.arc(sx1, sy1, 1, 0, Math.PI*2);
                                ctx.fill();
                            } else {
                                ctx.beginPath();
                                ctx.moveTo(sx1, sy1);
                                ctx.lineTo(sx2, sy2);
                                ctx.stroke();
                            }
                        }
                    }
                }

                // Draw Needle Shadow
                ctx.shadowColor = 'rgba(0,0,0,0.5)';
                ctx.shadowBlur = 5;
                ctx.shadowOffsetX = 3;
                ctx.shadowOffsetY = 3;
                
                // Draw Needle
                const pointerStyle = styleOv.Pointer_Style || config?.Pointer_Style || 'line';
                const needleLen = arcRadius * (styleOv.needle_length_factor || 0.95);
                ctx.strokeStyle = config?.pointer_colour || '#fff';
                ctx.fillStyle = config?.pointer_colour || '#fff';
                
                const nx = centerX + needleLen * Math.cos(needleAngleRad);
                const ny = centerY + needleLen * Math.sin(needleAngleRad);
                
                if (pointerStyle === 'spade') {
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.moveTo(centerX, centerY);
                    const bw = 3;
                    const p1x = centerX + (needleLen * 0.8) * Math.cos(needleAngleRad - 0.05);
                    const p1y = centerY + (needleLen * 0.8) * Math.sin(needleAngleRad - 0.05);
                    const p2x = centerX + (needleLen * 0.8) * Math.cos(needleAngleRad + 0.05);
                    const p2y = centerY + (needleLen * 0.8) * Math.sin(needleAngleRad + 0.05);
                    ctx.lineTo(p1x, p1y);
                    ctx.lineTo(nx, ny);
                    ctx.lineTo(p2x, p2y);
                    ctx.closePath();
                    ctx.fill();
                } else if (pointerStyle === 'knife-edge') {
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.moveTo(centerX - 2, centerY);
                    ctx.lineTo(nx, ny);
                    ctx.lineTo(centerX + 2, centerY);
                    ctx.closePath();
                    ctx.fill();
                } else {
                    ctx.lineWidth = config?.needle_thickness || 2;
                    ctx.lineCap = 'round';
                    ctx.beginPath();
                    ctx.moveTo(centerX, centerY);
                    ctx.lineTo(nx, ny);
                    ctx.stroke();
                }

                // Clear shadow for pivot
                ctx.shadowColor = 'transparent';

                // Draw Pivot Base
                const pivotRadius = config?.Pivot_size || config?.pivot_size || 12;
                ctx.fillStyle = config?.Pivot_colour || '#000';
                ctx.beginPath();
                ctx.arc(centerX, centerY, pivotRadius, 0, Math.PI * 2);
                ctx.fill();
                ctx.strokeStyle = '#444';
                ctx.lineWidth = 2;
                ctx.stroke();
                
                ctx.fillStyle = '#888';
                ctx.beginPath();
                ctx.arc(centerX, centerY, pivotRadius * 0.3, 0, Math.PI * 2);
                ctx.fill();
            }

            animationFrameId = requestAnimationFrame(render);
        };

        render();

        return () => {
            cancelAnimationFrame(animationFrameId);
        };
    }, [min, max, width, height, config]);
}

const NeedleMeter = ({ value, config }) => {
    const min = config?.domain?.primary?.min !== undefined ? config.domain.primary.min : -60;
    const max = config?.domain?.primary?.max !== undefined ? config.domain.primary.max : 10;
    
    const width = config?.geometry?.width || config?.layout?.width || 150;
    const height = config?.geometry?.height || config?.layout?.height || 150;

    const canvasRef = React.useRef(null);
    const rawValueRef = React.useRef(value !== undefined && value !== null ? value : min);

    React.useEffect(() => {
        rawValueRef.current = value !== undefined && value !== null ? value : min;
    }, [value, min]);

    useNeedleBallistics(rawValueRef, canvasRef, min, max, width, height, config);

    const title = config?.label?.En || config?.label_active?.En;

    return (
        <div style={{ 
            border: '2px solid #222', 
            padding: '2px', 
            backgroundColor: '#1a1a1a', 
            borderRadius: '4px',
            boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.8)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            width: width,
            height: height,
            position: 'relative', // Needed for absolute positioning of title
            overflow: 'hidden' // Ensure content stays within bounds
        }}>
            <canvas 
                ref={canvasRef} 
                width={width} 
                height={height} 
                style={{ display: 'block', width: '100%', height: '100%' }}
            />
            {title && (
                <div style={{ 
                    position: 'absolute', 
                    bottom: '10px', // Position at the bottom
                    left: '50%',
                    transform: 'translateX(-50%)',
                    color: '#aaa', 
                    fontSize: '11px', 
                    fontWeight: 'bold',
                    backgroundColor: 'rgba(0,0,0,0.5)',
                    padding: '2px 6px',
                    borderRadius: '3px'
                }}>
                    {title}
                </div>
            )}
        </div>
    );
};
window.NeedleMeter = NeedleMeter;