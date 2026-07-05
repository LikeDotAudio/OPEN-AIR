/**
 * Header: LTPFader.jsx
 * Purpose: LTPFader component or utility.
 * Description: Handles logic and rendering for LTPFader component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// LTPFader — Linear Travelling Potentiometer
// Author: Anthony Peter Kuzub (original concept) / refactor 20260526
//
// Architecture
//   - The whole widget (rail, track, ticks, master fill, the travelling cap
//     and its rotational indicator, numerics) is rendered in a single
//     <canvas>. This mirrors the standalone LTPWidget demo which draws the
//     cap directly so the LINEAR travel AND the ROTATIONAL value are shown
//     together as one "travelling potentiometer".
//       * Linear value  → cap Y position on the rail.
//       * Rotational value (rotVal, -100..100) → indicator angle (+/-135deg).
//   - Interaction (on the canvas):
//       * Drag the cap        → adjust linear value.
//       * Alt + drag the cap  → adjust rotation (pan/param).
//       * Double-click cap    → "pan latch": drag rotates until pointer up.
//       * Freestyle mode      → a single drag adjusts BOTH at once.
//       * Drag the bare rail  → jump linear value; Alt-click rail → default.
//       * Wheel               → fine-tune linear; Alt + wheel → fine rotation.
//   - Compound state shape: { value: linearVal, rotValue: rotPct }.
//
// Schema (per-LTP):
//   fader_config.domain.{min,max}           — linear travel range
//   fader_config.value.default_value        — linear default (alt-click rail)
//   knob_config.cap_radius                  — cap pixel radius
//   knob_config.cap_color                   — cap body fill
//   knob_config.cap_outline_color           — cap indicator/accent colour
//   cosmetics.colors.highlight              — rail master-fill colour
//   interaction.freestyle                   — freestyle (both-at-once) mode

// Inline comment: Logic for LTPFader
const LTPFader = ({ config, value, rotValue, onChange }) => {
    const canvasRef = React.useRef(null);
    const wrapperRef = React.useRef(null);
    const dragRef = React.useRef({ active: false, mode: 'linear', startX: 0, startY: 0, startLin: 0, startRot: 0, isMod: false });
    const [dragMode, setDragMode] = React.useState(null); // 'rail' | 'linear' | 'rot' | 'both'
    const [panLatch, setPanLatch] = React.useState(false);

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

    // Rotational domain (rotVal maps -100..100 → -135..135 degrees).
    const rotMin = -100;
    const rotMax = 100;
    const freestyle = !!(config?.interaction?.freestyle || fc?.freestyle || config?.freestyle);

    // Cap cosmetics (demo body is a light disc with an orange indicator).
    const capRadius = kc?.cap_radius || 18;
    const capBody   = kc?.cap_color || '#dcdcdc';
    const capAccent = kc?.cap_outline_color || railColor;

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

    // -- Rail + travelling cap render (canvas) --------------------------------
    const draw = (ctx) => {
        const cx = width / 2;
        const isNarrow = width < 50;

        // Rotation is "active" (draw the long sweep line) when we're adjusting
        // the pot: pan-latch on, or dragging in a rotation-capable mode.
        const isAdjustingPot = panLatch || dragMode === 'rot' || dragMode === 'both';

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
        ctx.strokeStyle = freestyle ? '#FF5555' : railColor;
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.moveTo(cx, height - 20);
        ctx.lineTo(cx, handleY);
        ctx.stroke();

        // Tick scale
        const range = max - min;
        const steps = isNarrow ? 5 : 10;
        ctx.strokeStyle = '#666';
        ctx.lineWidth = 1;
        ctx.font = isNarrow ? '7px Arial' : '10px Arial';
        ctx.fillStyle = '#888';
        ctx.textAlign = 'left';
        for (let i = 0; i <= steps; i++) {
            const norm = i / steps;
            const y = 20 + (height - 40) * (1.0 - norm);
            const val = min + (norm * range);
            const tw = isNarrow ? 5 : 10;
            ctx.beginPath();
            ctx.moveTo(cx - tw, y);
            ctx.lineTo(cx + tw, y);
            ctx.stroke();
            if (i % 2 === 0 && !isNarrow) {
                ctx.fillText(val.toFixed(0), cx + 15, y + 3);
            }
        }

        // -- Travelling cap ---------------------------------------------------
        // Cap body (glows when pan-latched).
        if (panLatch) {
            ctx.save();
            ctx.shadowColor = '#33A1FD';
            ctx.shadowBlur = 15;
            ctx.fillStyle = '#fff';
        } else {
            ctx.fillStyle = capBody;
        }
        ctx.beginPath();
        ctx.arc(cx, handleY, capRadius, 0, Math.PI * 2);
        ctx.fill();
        if (panLatch) ctx.restore();

        // Rotation indicator: rotVal (-100..100) → +/-135deg. When adjusting
        // the pot the line extends 10x so the sweep is legible off the cap.
        const angle = (currentRotVal / 100) * 135;
        const rad = (angle - 90) * Math.PI / 180;
        const drawLen = isAdjustingPot ? capRadius * 10 : capRadius;
        const px = cx + drawLen * Math.cos(rad);
        const py = handleY + drawLen * Math.sin(rad);
        ctx.strokeStyle = capAccent;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(cx, handleY);
        ctx.lineTo(px, py);
        ctx.stroke();

        // Center dot
        ctx.fillStyle = capAccent;
        ctx.beginPath();
        ctx.arc(cx, handleY, 3, 0, Math.PI * 2);
        ctx.fill();

        // -- Numerics ---------------------------------------------------------
        if (!isNarrow) {
            if (showVal) {
                ctx.fillStyle = '#fff';
                ctx.font = '10px Arial';
                ctx.textAlign = 'right';
                const lTxt = `L: ${linearVal.toFixed(1)}${showUnits && unitText ? ' ' + unitText : ''}`;
                ctx.fillText(lTxt, cx - 25, handleY + 4);
                ctx.textAlign = 'left';
                ctx.fillText(`R: ${currentRotVal.toFixed(0)}`, cx + 25, handleY + 4);
            }
            if (freestyle) {
                ctx.textAlign = 'center';
                ctx.fillStyle = '#FF5555';
                ctx.font = 'bold 10px Arial';
                ctx.fillText('FREESTYLE', cx, height - 5);
            }
        } else if (showVal) {
            ctx.fillStyle = '#000';
            ctx.textAlign = 'center';
            ctx.font = '7px Arial';
            ctx.fillText(`${linearVal.toFixed(0)}`, cx, handleY + 3);
        }
    };

    React.useEffect(() => {
        if (canvasRef.current) {
            const ctx = canvasRef.current.getContext('2d');
            draw(ctx);
        }
    }, [linearVal, currentRotVal, width, height, railColor, dragMode, panLatch, freestyle]);

    // -- Interaction ----------------------------------------------------------
    const getPos = (e) => {
        const cv = canvasRef.current;
        const rect = cv.getBoundingClientRect();
        const sx = cv.width / (rect.width || 1);
        const sy = cv.height / (rect.height || 1);
        return { x: (e.clientX - rect.left) * sx, y: (e.clientY - rect.top) * sy };
    };
    const isOverHandle = (x, y) => {
        const hy = getHandleY(linearVal);
        const cx = width / 2;
        const hit = capRadius * 1.5;   // generous hit area (touch-friendly)
        return Math.hypot(x - cx, y - hy) <= hit;
    };

    const handlePointerDown = (e) => {
        const { x, y } = getPos(e);
        try { canvasRef.current.setPointerCapture(e.pointerId); } catch (_) {}
        if (isOverHandle(x, y)) {
            const mode = freestyle ? 'both' : (panLatch || e.altKey ? 'rot' : 'linear');
            dragRef.current = { active: true, mode, startX: x, startY: y, startLin: linearVal, startRot: currentRotVal, isMod: e.altKey };
            setDragMode(mode);
        } else {
            // Bare rail: alt → snap to default, otherwise absolute-Y jump/drag.
            if (e.altKey) {
                onChange && onChange({ value: defaultVal, rotValue: currentRotVal });
                return;
            }
            dragRef.current = { active: true, mode: 'rail', startX: x, startY: y, startLin: linearVal, startRot: currentRotVal, isMod: false };
            setDragMode('rail');
            const v = Math.max(min, Math.min(max, getValFromY(y)));
            onChange && onChange({ value: v, rotValue: currentRotVal });
        }
    };

    const handlePointerMove = (e) => {
        const d = dragRef.current;
        if (!d.active) return;
        const { x, y } = getPos(e);

        if (d.mode === 'rail') {
            const v = Math.max(min, Math.min(max, getValFromY(y)));
            onChange && onChange({ value: v, rotValue: currentRotVal });
            return;
        }

        // Mid-drag mode switch when Alt is toggled (handle grab, non-freestyle).
        if (!freestyle && !panLatch) {
            const nowMod = e.altKey;
            if (nowMod !== d.isMod) {
                d.startX = x; d.startY = y; d.startLin = linearVal; d.startRot = currentRotVal;
                d.isMod = nowMod; d.mode = nowMod ? 'rot' : 'linear';
                setDragMode(d.mode);
            }
        }

        let nextLin = linearVal;
        let nextRot = currentRotVal;
        const rotActive = freestyle || d.mode === 'rot' || panLatch;
        const linActive = freestyle || (d.mode === 'linear' && !panLatch);

        if (rotActive) {
            const dx = x - d.startX;
            let change = dx * 0.5;
            if (freestyle) change /= 2;
            nextRot = Math.max(rotMin, Math.min(rotMax, d.startRot + change));
        }
        if (linActive) {
            const dy = y - d.startY;
            let change = -(dy / (height - 40)) * (max - min);
            if (freestyle) change /= 2;
            nextLin = Math.max(min, Math.min(max, d.startLin + change));
        }
        onChange && onChange({ value: nextLin, rotValue: nextRot });
    };

    const handlePointerUp = (e) => {
        dragRef.current.active = false;
        setDragMode(null);
        if (panLatch) setPanLatch(false);
        if (canvasRef.current) {
            try { canvasRef.current.releasePointerCapture(e.pointerId); } catch (_) {}
        }
    };

    const handleDoubleClick = (e) => {
        const { x, y } = getPos(e);
        if (isOverHandle(x, y)) setPanLatch(true);
    };

    // Native, non-passive wheel so preventDefault works (fine-tune fader).
    React.useEffect(() => {
        const cv = canvasRef.current;
        if (!cv) return;
        const onWheel = (e) => {
            e.preventDefault();
            const delta = Math.sign(e.deltaY) * -1; // up is positive
            if (e.altKey) {
                const nr = Math.max(rotMin, Math.min(rotMax, currentRotVal + delta * 5));
                onChange && onChange({ value: linearVal, rotValue: nr });
            } else {
                const nl = Math.max(min, Math.min(max, linearVal + delta * ((max - min) / 50)));
                onChange && onChange({ value: nl, rotValue: currentRotVal });
            }
        };
        cv.addEventListener('wheel', onWheel, { passive: false });
        return () => cv.removeEventListener('wheel', onWheel);
    }, [linearVal, currentRotVal, min, max]);

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
            </div>
            <div style={{ position: 'relative', width, height }}>
                <canvas
                    ref={canvasRef}
                    width={width}
                    height={height}
                    onPointerDown={handlePointerDown}
                    onPointerMove={handlePointerMove}
                    onPointerUp={handlePointerUp}
                    onDoubleClick={handleDoubleClick}
                    style={{
                        cursor: freestyle ? 'move' : 'ns-resize',
                        backgroundColor: '#222',
                        boxShadow: 'inset 0 0 5px rgba(0,0,0,0.5)',
                        borderRadius: 4,
                        touchAction: 'none',
                        display: 'block',
                    }}
                />
            </div>
        </div>
    );
};

window.LTPFader = LTPFader;
