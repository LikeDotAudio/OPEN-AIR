/**
 * MeterBarGraph Architecture (Separated Concerns)
 * 1. MeterBallistics: Hook for smoothing and peak hold logic.
 * 2. MeterScale: Rendering ticks, grid, and labels.
 * 3. MeterBody: The visual bar (fills, indicator, peak flag).
 * 4. Main Orchestrator: Combines elements and handles orientation.
 */

// --- 1. BALLISTICS ENGINE ---
function useMeterBallistics(rawValue, config, min, max) {
    const [displayValue, setDisplayValue] = React.useState(min);
    const [peakValue, setPeakValue] = React.useState(min);
    const [overloadFade, setOverloadFade] = React.useState(0);
    const lastTimeRef = React.useRef(Date.now());
    const peakHoldTimerRef = React.useRef(0);
    const barTargetRef = React.useRef(min);  // latched peak the bar rises to
    const lastRawRef = React.useRef(min);     // last raw sample (detect new samples)

    React.useEffect(() => {
        let animFrame;
        const update = () => {
            const now = Date.now();
            const dt = (now - lastTimeRef.current) / 1000;
            lastTimeRef.current = now;

            const ballistics = config.ballistics || config.dynamics || {};
            const overload = config.overload || ballistics.peak || config.peak || {};

            const attackMs = ballistics.attack_ms || ballistics.Attack_ms || 10;
            const releaseMs = ballistics.release_ms || ballistics.Release_ms || 300;
            const peakHoldMs = overload.peak_hold_ms || overload.overload_hold_ms || 1000;
            const overloadFadeMs = overload.overload_fade_ms || 500;

            const attackStep = dt / (attackMs / 1000 || 0.01);
            const releaseStep = dt / (releaseMs / 1000 || 0.01);

            // Peak-hold-release: a new sample latches a peak to attack up to, then
            // the bar falls back to the floor (min) at the release rate (so it
            // decays to zero/rest instead of holding the value).
            const eps = (max - min) * 0.005;
            if (rawValue !== lastRawRef.current) { lastRawRef.current = rawValue; barTargetRef.current = rawValue; }
            setDisplayValue(prev => {
                let next = prev;
                if (prev < barTargetRef.current - eps) {
                    next += (barTargetRef.current - prev) * Math.min(1, attackStep);
                } else {
                    barTargetRef.current = min; // consume the peak; release to floor
                    next -= (prev - min) * Math.min(1, releaseStep);
                }
                return Math.max(min, Math.min(max, next));
            });

            setPeakValue(prev => {
                let nextPeak = prev;
                if (rawValue > prev) {
                    nextPeak = rawValue;
                    peakHoldTimerRef.current = peakHoldMs;
                } else {
                    if (peakHoldTimerRef.current > 0) {
                        peakHoldTimerRef.current -= dt * 1000;
                    } else {
                        nextPeak -= (max - min) * (dt / 2.0); // Slow decay after hold
                    }
                }
                return Math.max(min, Math.min(max, nextPeak));
            });

            setOverloadFade(prev => {
                if (rawValue >= 0) return 1.0;
                return Math.max(0, prev - (dt / (overloadFadeMs / 1000 || 0.5)));
            });

            animFrame = requestAnimationFrame(update);
        };
        update();
        return () => cancelAnimationFrame(animFrame);
    }, [rawValue, config, min, max]);

    return { displayValue, peakValue, overloadFade };
}

// --- 2. SCALE RENDERING (Ticks & Labels) ---
const MeterScale = ({ config, layout, min, max }) => {
    const { isVertical, barX, barY, baseLen, barThick, tickStart, tickDir } = layout;
    const cosmetics = config.cosmetics || {};
    const colors = cosmetics.colors || {};
    const scale = config.scale || {};
    const labels_cfg = config.labels || {};
    
    const showTicks = config.show_ticks !== undefined ? config.show_ticks : (config.show_Ticks !== undefined ? config.show_Ticks : (scale.show || false));
    const showLabels = labels_cfg.show_scale_labels !== undefined ? labels_cfg.show_scale_labels : (config.show_scale_labels !== false);
    const tickSize = config.tick_size || config.geometry?.tick_size || 5;
    const tickColor = colors.tick || '#E0E0E0';
    const subTickColor = colors.sub_tick || colors.tick || '#888';
    const textColor = colors.scale || colors.tick || '#E0E0E0';
    const fontSize = config.font_size || config.geometry?.font_size || 8;
    
    if (!showTicks && !showLabels) return null;

    const elements = [];
    const numMain = 5;

    for (let i = 0; i <= numMain; i++) {
        const norm = i / numMain;
        const val = min + norm * (max - min);
        const pos = norm * baseLen;

        let tx1, ty1, tx2, ty2, lx, ly, anchor;

        if (!isVertical) {
            tx1 = barX + pos; ty1 = tickStart;
            tx2 = tx1; ty2 = tickStart + (tickSize * tickDir);
            lx = tx2; ly = ty2 + (5 * tickDir);
            anchor = tickDir === 1 ? 'hanging' : 'baseline';
        } else {
            tx1 = tickStart; ty1 = barY + (baseLen - pos);
            tx2 = tickStart + (tickSize * tickDir); ty2 = ty1;
            lx = tx2 + (5 * tickDir); ly = ty2;
            anchor = 'middle';
        }

        if (showTicks) {
            elements.push(<line key={`t-${i}`} x1={tx1} y1={ty1} x2={tx2} y2={ty2} stroke={tickColor} strokeWidth="1.5" />);
        }
        if (showLabels && fontSize > 0) {
            elements.push(
                <text key={`l-${i}`} x={lx} y={ly} fill={textColor} fontSize={fontSize} 
                      textAnchor={!isVertical ? 'middle' : (tickDir === 1 ? 'start' : 'end')} 
                      dominantBaseline={anchor}>
                    {Math.round(val)}
                </text>
            );
        }

        // Subticks
        const styleOv = cosmetics.style_overrides || {};
        const subCount = styleOv.sub_ticks || config.sub_ticks || 0;
        if (i < numMain && subCount > 0) {
            for (let j = 1; j <= subCount; j++) {
                const sNorm = norm + (1/numMain) * (j / (subCount + 1));
                const sPos = sNorm * baseLen;
                let stx1, sty1, stx2, sty2;
                if (!isVertical) {
                    stx1 = barX + sPos; sty1 = tickStart;
                    stx2 = stx1; sty2 = tickStart + (tickSize * 0.5 * tickDir);
                } else {
                    stx1 = tickStart; sty1 = barY + (baseLen - sPos);
                    stx2 = tickStart + (tickSize * 0.5 * tickDir); sty2 = sty1;
                }
                elements.push(<line key={`st-${i}-${j}`} x1={stx1} y1={sty1} x2={stx2} y2={sty2} stroke={subTickColor} strokeWidth="1" />);
            }
        }
    }

    return <g className="meter-scale">{elements}</g>;
};

// --- 3. METER BODY (Fills & Faders) ---
const MeterBody = ({ config, layout, values, min, max }) => {
    const { isVertical, barX, barY, baseLen, barThick } = layout;
    const { displayValue, peakValue, overloadFade } = values;
    
    const cosmetics = config.cosmetics || {};
    const colors = cosmetics.colors || {};
    const styleFlags = cosmetics.style_flags || {};
    const ballistics = config.ballistics || {};
    const overload = config.overload || ballistics.peak || {};

    const lowerColor = colors.lower || colors.primary || 'green';
    const middleColor = colors.middle || colors.secondary || 'yellow';
    const upperColor = colors.upper || colors.alert || 'red';
    const peakColor = colors.Peak_alert || colors.peak_alert || 'red';
    
    const midRange = config.middle_range !== undefined ? config.middle_range : (config.scale?.middle_range || -10);
    const upperRange = config.upper_range !== undefined ? config.upper_range : (config.scale?.upper_range || 0);
    
    const getPos = (v) => Math.max(0, Math.min(baseLen, ((v - min) / ((max - min) || 1)) * baseLen));
    
    const pos = getPos(displayValue);
    const midPos = getPos(midRange);
    const upperPos = getPos(upperRange);
    const peakPos = getPos(peakValue);

    const fillShape = styleFlags.fill_shape !== false && config.fill_shape !== false;

    const renderRect = (vStart, vEnd, color, opacity = 1) => {
        if (vStart >= vEnd) return null;
        let rx, ry, rw, rh;
        if (!isVertical) {
            rx = barX + vStart; ry = barY;
            rw = vEnd - vStart; rh = barThick;
        } else {
            rx = barX; ry = barY + (baseLen - vEnd);
            rw = barThick; rh = vEnd - vStart;
        }
        return <rect x={rx} y={ry} width={rw} height={rh} fill={color} fillOpacity={opacity} />;
    };

    const renderPeakFlag = (p) => {
        if (!overload.Peak_flag && !config.peak_flag) return null;
        const fs = 6;
        let pts = "";
        if (!isVertical) {
            const tipY = layout.tickDir === 1 ? barY + barThick : barY;
            const tipX = barX + p;
            pts = layout.tickDir === 1 ? `${tipX},${tipY} ${tipX-fs/2},${tipY+fs} ${tipX+fs/2},${tipY+fs}` : `${tipX},${tipY} ${tipX-fs/2},${tipY-fs} ${tipX+fs/2},${tipY-fs}`;
        } else {
            const tipY = barY + baseLen - p;
            const tipX = layout.tickDir === 1 ? barX + barThick : barX;
            pts = layout.tickDir === 1 ? `${tipX},${tipY} ${tipX+fs},${tipY-fs/2} ${tipX+fs},${tipY+fs/2}` : `${tipX},${tipY} ${tipX-fs},${tipY-fs/2} ${tipX-fs},${tipY+fs/2}`;
        }
        return <polygon points={pts} fill={peakColor} />;
    };

    return (
        <g className="meter-body">
            {/* Background Track */}
            {renderRect(0, baseLen, config.bar_track_bg || '#111')}
            
            {/* Fills / Zones */}
            {fillShape ? (
                <>
                    {renderRect(0, Math.min(pos, midPos), lowerColor)}
                    {renderRect(midPos, Math.min(pos, upperPos), middleColor)}
                    {renderRect(upperPos, pos, upperColor)}
                </>
            ) : (
                /* Discrete Indicator Style */
                renderRect(pos - 2, pos + 2, colors.pointer || '#fff')
            )}
            
            {/* Internal Grid Overlay */}
            {(styleFlags.show_grid || config.tick_grid_overlay || config.show_grid) && (
                <g stroke="#000" strokeWidth="1" opacity="0.4">
                    {[0, 0.2, 0.4, 0.6, 0.8, 1.0].map(n => {
                        const p = n * baseLen;
                        return !isVertical ? 
                            <line key={n} x1={barX + p} y1={barY} x2={barX + p} y2={barY + barThick} /> :
                            <line key={n} x1={barX} y1={barY + p} x2={barX + barThick} y2={barY + p} />;
                    })}
                </g>
            )}

            {/* Peak Indicator (Line or Rect) */}
            {(overload.Peak_display !== false && config.peak_display !== false) && (
                overload.Peak_display_line_style === 'rect' ? 
                renderRect(peakPos - 4, peakPos, peakColor, 0.8) :
                renderRect(peakPos - 1, peakPos + 1, peakColor)
            )}
            
            {/* Peak Flag (Triangle) */}
            {renderPeakFlag(peakPos)}
            
            {/* Overload LED */}
            {(overload.show_peak_hold !== false && config.show_peak_hold !== false) && (
                <rect 
                    x={layout.ledX} y={layout.ledY} width={layout.ledSize} height={layout.ledSize} 
                    fill={overloadFade > 0 ? peakColor : '#333'} 
                    fillOpacity={0.2 + overloadFade * 0.8}
                    stroke="#000" strokeWidth="0.5"
                />
            )}
        </g>
    );
};

// --- 4. MAIN ORCHESTRATOR ---
const MeterBarGraph = ({ value, config }) => {
    const c = config || {};
    const geom = c.geometry || {};
    const cosmetics = c.cosmetics || {};
    const colors = cosmetics.colors || {};
    
    // Domain Extraction
    const d = c.domain?.primary || c.domain || {};
    const min = d.min !== undefined ? d.min : (c.min_val || -40);
    const max = d.max !== undefined ? d.max : (c.max_val || 10);
    
    // Orientation & Geometry
    const orientation = (geom.orientation || c.orientation || 'vertical').toLowerCase();
    const isVertical = orientation.startsWith('vert');
    
    const baseW = geom.width || c.width || (isVertical ? 20 : 200);
    const baseH = geom.height || c.height || (isVertical ? 200 : 20);
    
    // Layout Logic (Mirroring Python side_a/side_b padding)
    const scalePos = (c.scale_position || c.labels?.label_position || (isVertical ? 'right' : 'bottom')).toLowerCase();
    const tickSize = c.tick_size || geom.tick_size || 5;
    const fontSize = c.font_size || geom.font_size || 8;
    const labelPad = fontSize > 0 ? (isVertical ? fontSize * 3 : fontSize + 5) : 0;
    
    let sideA = 0, sideB = 0;
    if (scalePos === 'top' || scalePos === 'left') sideA = tickSize + labelPad;
    if (scalePos === 'bottom' || scalePos === 'right') sideB = tickSize + labelPad;
    
    // Final Canvas dimensions
    const totalW = isVertical ? (baseW + sideA + sideB) : (baseW + 40);
    const totalH = isVertical ? (baseH + 40) : (baseH + sideA + sideB);
    
    const barX = isVertical ? sideA : 20;
    const barY = isVertical ? 20 : sideA;
    const baseLen = isVertical ? baseH : baseW;
    const barThick = isVertical ? baseW : baseH;
    
    const tickStart = isVertical ? (scalePos === 'right' ? barX + barThick : barX) : (scalePos === 'bottom' ? barY + barThick : barY);
    const tickDir = (scalePos === 'right' || scalePos === 'bottom') ? 1 : -1;
    
    const peakLedSize = geom.peak_size > 0 ? geom.peak_size : Math.min(barThick, 12);
    const ledX = isVertical ? (barX + barThick/2 - peakLedSize/2) : (barX + baseLen + 8);
    const ledY = isVertical ? (barY - peakLedSize - 8) : (barY + barThick/2 - peakLedSize/2);

    const layout = { isVertical, barX, barY, baseLen, barThick, tickStart, tickDir, ledX, ledY, ledSize: peakLedSize };

    // State & Ballistics
    const rawVal = typeof value === 'number' ? value : (typeof value === 'string' ? parseFloat(value) : min);
    const ballistics = useMeterBallistics(rawVal, c, min, max);

    // Header Label
    const [lang] = window.useMqttLang ? window.useMqttLang() : ['En'];
    const title = c.label?.[lang] || c.label?.En || c.label_active?.[lang] || c.label_active?.En || "";
    const showTitle = c.show_label !== false && c.labels?.show_label !== false;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '5px' }}>
            {(showTitle && title) && (
                <div style={{ color: colors.label || '#E0E0E0', fontSize: '10px', fontWeight: 'bold', marginBottom: '5px' }}>
                    {title.toUpperCase()}
                </div>
            )}
            <svg width={totalW} height={totalH} viewBox={`0 0 ${totalW} ${totalH}`} style={{ overflow: 'visible' }}>
                <MeterBody config={c} layout={layout} values={ballistics} min={min} max={max} />
                <MeterScale config={c} layout={layout} min={min} max={max} />
            </svg>
        </div>
    );
};

window.MeterBarGraph = MeterBarGraph;