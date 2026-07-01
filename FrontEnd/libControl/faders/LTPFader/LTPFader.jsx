// LTPFader — Linear Travelling Potentiometer
// Author: Anthony Peter Kuzub (original concept) / refactor 20260526
//
// Architecture
//   - The vertical rail (background, track, ticks, master fill, numerics) is
//     rendered in a <canvas>. Drag the rail (i.e. anywhere outside the cap)
//     to set the linear value.
//   - The cap itself is a real <window.Knob>, absolutely positioned at the
//     handle's Y. The rotation drag is the Knob's native gesture. This lets
//     ANY of the 9 cap styles (standard, chicken, marconi, british, pedal,
//     1176, api, fender, moog, wbs-elma, plus panner/dial/gear) be used on
//     an LTP — read from `knob_style`/`knob_shape` in the schema.
//   - Compound state shape: { value: linearVal, rotValue: rotPct }.
//
// Schema (per-LTP):
//   fader_config.domain.{min,max}           — linear travel range
//   fader_config.value.default_value        — linear default (alt-click rail)
//   knob_config.knob_style                  — cap style (chicken | marconi | …)
//   knob_config.cap_radius                  — cap pixel radius (knob size = 2× this)
//   knob_config.cap_color                   — cap fill
//   knob_config.cap_outline_color           — cap indicator/accent
//   knob_config.knob_teeth                  — for gear shape
//   style.knob_shape                        — circle | octagon | gear
//   style.pointer_style, style.arc_width    — Knob cosmetics passthrough
//   cosmetics.colors.highlight              — rail master-fill colour

const LTPFader = ({ config, value, rotValue, onChange }) => {
    const canvasRef = React.useRef(null);
    const wrapperRef = React.useRef(null);
    const [dragging, setDragging] = React.useState(false);

    // Schema-pillar pulls (with legacy fallbacks).
    const fc = config?.fader_config || {};
    const kc = config?.knob_config || {};
    const st = config?.style || {};

    const min = fc?.domain?.min !== undefined ? fc.domain.min
              : (config?.min !== undefined ? config.min : 0);
    const max = fc?.domain?.max !== undefined ? fc.domain.max
              : (config?.max !== undefined ? config.max : 100);
    const defaultVal = fc?.value?.default_value !== undefined ? fc.value.default_value : ((min + max) / 2);
    const width  = config?.layout?.width  || config?.width  || 100;
    const height = config?.layout?.height || config?.height || 400;
    const railColor = fc?.cosmetics?.colors?.highlight || kc?.cap_outline_color || '#f4902c';
    const unitText = fc?.unit_text || '';
    const showVal   = fc?.readout?.show_value !== false;
    const showUnits = fc?.readout?.show_units !== false;

    const knobStyle = (kc?.knob_style || st?.knob_style || 'standard').toLowerCase();
    const isPanner  = knobStyle === 'panner';
    const capRadius = kc?.cap_radius || 22;
    const capSize   = capRadius * 2 + 24;        // padding for arc + ticks

    // Compound value extraction.
    const getNum = (v, fb) => (typeof v === 'number' ? v : (typeof v === 'string' && !Number.isNaN(parseFloat(v)) ? parseFloat(v) : fb));
    let linearVal = (min + max) / 2;
    let currentRotVal = 0;
    if (value && typeof value === 'object' && !Array.isArray(value)) {
        linearVal = getNum(value.value, linearVal);
        currentRotVal = getNum(value.rotValue, currentRotVal);
    } else {
        linearVal = getNum(value, linearVal);
        currentRotVal = getNum(rotValue, currentRotVal);
    }

    // -- Coordinate mapping ---------------------------------------------------
    const getHandleY = (val) => {
        const range = (max - min) || 1;
        const norm = (val - min) / range;
        const drawH = height - 40;
        return 20 + drawH * (1.0 - norm);
    };
    const getValFromY = (y) => {
        const drawH = height - 40;
        const norm = (drawH - (y - 20)) / drawH;
        return min + (norm * (max - min));
    };

    // -- Rail render (canvas) -------------------------------------------------
    const draw = (ctx) => {
        const cx = width / 2;
        ctx.fillStyle = '#222';
        ctx.fillRect(0, 0, width, height);

        // Track
        ctx.strokeStyle = '#444';
        ctx.lineWidth = 4;
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.moveTo(cx, 20);
        ctx.lineTo(cx, height - 20);
        ctx.stroke();

        // Master fill (bottom → handle)
        const handleY = getHandleY(linearVal);
        ctx.strokeStyle = railColor;
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.moveTo(cx, height - 20);
        ctx.lineTo(cx, handleY);
        ctx.stroke();

        // Tick scale
        const range = max - min;
        const isNarrow = width < 70;
        const steps = isNarrow ? 5 : 10;
        ctx.strokeStyle = '#666';
        ctx.lineWidth = 1;
        ctx.font = isNarrow ? '8px Arial' : '10px Arial';
        ctx.fillStyle = '#888';
        ctx.textAlign = 'left';
        for (let i = 0; i <= steps; i++) {
            const norm = i / steps;
            const y = 20 + (height - 40) * (1.0 - norm);
            const val = min + (norm * range);
            const tw = isNarrow ? 5 : 9;
            ctx.beginPath();
            ctx.moveTo(cx - tw, y);
            ctx.lineTo(cx + tw, y);
            ctx.stroke();
            if (i % 2 === 0 && !isNarrow) {
                ctx.fillText(val.toFixed(0), cx + 14, y + 3);
            }
        }

        // Linear value readout (below the cap)
        if (showVal && !isNarrow) {
            ctx.fillStyle = '#fff';
            ctx.textAlign = 'center';
            ctx.font = 'bold 11px Arial';
            const txt = `${linearVal.toFixed(1)}${showUnits && unitText ? ' ' + unitText : ''}`;
            ctx.fillText(txt, cx, Math.min(height - 6, handleY + capSize / 2 + 14));
        }
    };

    React.useEffect(() => {
        if (canvasRef.current) {
            const ctx = canvasRef.current.getContext('2d');
            draw(ctx);
        }
    }, [linearVal, currentRotVal, width, height, railColor]);

    // -- Rail interaction (linear) -------------------------------------------
    // Clicks on the cap go to the Knob (which absorbs them). Clicks anywhere
    // else on the canvas are rail clicks → set linear value.
    const railFromEvent = (e) => {
        const rect = canvasRef.current.getBoundingClientRect();
        const scaleY = rect.height / (canvasRef.current.offsetHeight || 1);
        const y = (e.clientY - rect.top) / scaleY;
        return Math.max(min, Math.min(max, getValFromY(y)));
    };
    const handleRailDown = (e) => {
        if (e.altKey) {
            // Alt-click rail → snap linear to default
            onChange && onChange({ value: defaultVal, rotValue: currentRotVal });
            return;
        }
        setDragging(true);
        canvasRef.current.setPointerCapture(e.pointerId);
        const v = railFromEvent(e);
        onChange && onChange({ value: v, rotValue: currentRotVal });
    };
    const handleRailMove = (e) => {
        if (!dragging) return;
        const v = railFromEvent(e);
        onChange && onChange({ value: v, rotValue: currentRotVal });
    };
    const handleRailUp = (e) => {
        setDragging(false);
        if (canvasRef.current) {
            try { canvasRef.current.releasePointerCapture(e.pointerId); } catch (_) {}
        }
    };

    // -- Cap (Knob overlay) ---------------------------------------------------
    // Build a Knob config from LTP keys so any of the 9 styles can be used.
    const rotMin = isPanner ? 0 : -100;
    const rotMax = isPanner ? 100 : 100;
    const knobCfg = {
        knob_style: knobStyle,
        min: rotMin,
        max: rotMax,
        width: capSize,
        height: capSize,
        arc_width: st?.arc_width,
        knob_teeth: kc?.knob_teeth || st?.knob_teeth,
        value: { default_value: 0 },
        cosmetics: {
            colors: {
                active: kc?.cap_outline_color || railColor,
                primary: kc?.cap_outline_color || railColor,
                secondary: '#444',
                track: '#3a3a3a',
            },
            styling: {
                knob_style: knobStyle,
                shape: (st?.knob_shape || st?.shape || 'circle'),
                fill_color: kc?.cap_color || '#1a1a1a',
                arc_width: st?.arc_width,
                teeth: kc?.knob_teeth || st?.knob_teeth,
                pointer_style: st?.pointer_style,
            },
            style_overrides: {
                knob_style: knobStyle,
                shape: (st?.knob_shape || st?.shape || 'circle'),
            },
            scale: { show: false },
        },
        // For panner: outputs [leftPct, rightPct]; we collapse to a single rot.
        interaction: { infinity: !!config?.interaction?.infinity },
    };

    const handleY = getHandleY(linearVal);
    const cx = width / 2;
    // Cap value: for non-panner use rotValue directly. For panner take the
    // pos and translate back-and-forth via the array protocol.
    const capValue = isPanner ? [50 - currentRotVal / 2, 50 + currentRotVal / 2] : currentRotVal;
    const onCapChange = (v) => {
        let nextRot = currentRotVal;
        if (isPanner && Array.isArray(v)) {
            // v = [left, right], both 0-100 with sum~=100. Recover rotPct in [-100..100].
            const r = Number(v[1]) - Number(v[0]);   // -100 (full L) → +100 (full R)
            nextRot = Math.max(-100, Math.min(100, r));
        } else {
            nextRot = Number(v);
        }
        onChange && onChange({ value: linearVal, rotValue: nextRot });
    };

    return (
        <div ref={wrapperRef} className="ltp-wrapper" style={{
            backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, '#3c3f41') : '#3c3f41'),
            border: '1px solid #555',
            padding: '8px',
            borderRadius: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            position: 'relative',
        }}>
            <div className="widget-label" style={{
                marginBottom: 6,
                fontWeight: 'bold',
                color: '#dcdcdc',
                fontSize: width < 50 ? 9 : 12,
                textAlign: 'center',
            }}>
                {String(
                    (config?.label?.active?.text?.En)
                    || (typeof config?.label === 'string' ? config.label : null)
                    || 'LTP'
                ).toUpperCase()}
                {kc?.knob_style && (
                    <div style={{ fontSize: 9, color: '#888', fontWeight: 'normal', textTransform: 'uppercase', letterSpacing: 1 }}>
                        {kc.knob_style}
                    </div>
                )}
            </div>
            <div style={{ position: 'relative', width, height }}>
                <canvas
                    ref={canvasRef}
                    width={width}
                    height={height}
                    onPointerDown={handleRailDown}
                    onPointerMove={handleRailMove}
                    onPointerUp={handleRailUp}
                    style={{
                        cursor: 'ns-resize',
                        backgroundColor: '#222',
                        borderRadius: 4,
                        touchAction: 'none',
                        display: 'block',
                    }}
                />
                <div style={{
                    position: 'absolute',
                    left: cx - capSize / 2,
                    top: handleY - capSize / 2,
                    width: capSize,
                    height: capSize,
                    pointerEvents: 'auto',
                }}>
                    {window.Knob
                        ? <window.Knob value={capValue} onChange={onCapChange} config={knobCfg} size={capSize} />
                        : <div style={{ width: capSize, height: capSize, borderRadius: '50%', background: kc?.cap_color || '#1a1a1a', border: `2px solid ${kc?.cap_outline_color || railColor}` }} />
                    }
                </div>
            </div>
        </div>
    );
};

window.LTPFader = LTPFader;
