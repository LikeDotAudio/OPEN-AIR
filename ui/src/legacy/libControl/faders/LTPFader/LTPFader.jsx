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
    const lastMiddleRef = React.useRef(0); // timestamp of last middle-press (double-click detect)
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
    const cfgWidth  = config?.layout?.width  || config?.width  || 100;
    const cfgHeight = config?.layout?.height || config?.height || 400;
    const [width, setWidth] = React.useState(typeof cfgWidth === 'number' ? cfgWidth : 100);
    const [height, setHeight] = React.useState(typeof cfgHeight === 'number' ? cfgHeight : 400);

    React.useLayoutEffect(() => {
        if (!wrapperRef.current) return;
        const needsObserver = typeof cfgWidth === 'string' || typeof cfgHeight === 'string';
        if (!needsObserver) {
            setWidth(cfgWidth);
            setHeight(cfgHeight);
            return;
        }
        const ro = new ResizeObserver(entries => {
            for (let entry of entries) {
                const rect = entry.contentRect;
                if (rect.width > 0) setWidth(rect.width);
                if (rect.height > 0) setHeight(rect.height);
            }
        });
        ro.observe(wrapperRef.current);
        return () => ro.disconnect();
    }, [cfgWidth, cfgHeight]);
    const railColor = fc?.cosmetics?.colors?.highlight || kc?.cap_outline_color || '#f4902c';
    const unitText = fc?.unit_text || '';
    const showVal   = fc?.readout?.show_value !== false;
    const showUnits = fc?.readout?.show_units !== false;

    // Dual-mode rotational pot. Mode 1 = primary rotation (e.g. Gain); Mode 2 =
    // secondary rotation (e.g. Q), toggled by double-clicking the cap. Both values
    // ride in the compound payload so nothing is lost when switching:
    //   { value:<linear>, rotValue:<mode1>, rotValue2:<mode2>, mode:1|2 }.
    const rotMin = kc?.rotation_min !== undefined ? kc.rotation_min : -100;
    const rotMax = kc?.rotation_max !== undefined ? kc.rotation_max : 100;
    const rot2Enabled = kc?.rotation2_min !== undefined || kc?.rotation2_max !== undefined || kc?.dual_pot === true;
    const rot2Min = kc?.rotation2_min !== undefined ? kc.rotation2_min : 0.1;
    const rot2Max = kc?.rotation2_max !== undefined ? kc.rotation2_max : 10;
    const rot2Default = kc?.rotation2_default !== undefined ? kc.rotation2_default : rot2Min;

    // Middle-button behaviour (configurable):
    //   single press + vertical drag → "free mode" fine-adjust of the position
    //   double middle-click        → normalize (recenter the active rotation)
    const midFine = kc?.middle_fine !== undefined ? kc.middle_fine : 300;         // px per unit-norm (higher = finer)
    const midDoubleMs = kc?.middle_double_ms !== undefined ? kc.middle_double_ms : 350;
    const midDoubleNormalizes = kc?.middle_double_normalize !== false;

    const freestyle = !!(config?.interaction?.freestyle || fc?.freestyle || config?.freestyle);
    const isHorizontal = width > height;

    // Cap cosmetics (demo body is a light disc with an accent indicator).
    const capRadius = kc?.cap_radius || 18;
    const capBody   = kc?.cap_color || '#dcdcdc';
    const capAccent = kc?.cap_outline_color || railColor;
    const capAccent2 = kc?.cap_color_2 || '#ffffff'; // Mode-2 (Q) cap colour

    // Compound value extraction (legacy scalar / {value,rotValue} still accepted).
    const getNum = (v, fb) => (typeof v === 'number' ? v : (typeof v === 'string' && !Number.isNaN(parseFloat(v)) ? parseFloat(v) : fb));
    let linearVal = (min + max) / 2;
    let gainVal = 0;         // mode-1 rotation
    let qVal = rot2Default;  // mode-2 rotation
    let potMode = 1;
    if (value && typeof value === 'object' && !Array.isArray(value)) {
        linearVal = getNum(value.value, linearVal);
        gainVal = getNum(value.rotValue, gainVal);
        qVal = getNum(value.rotValue2, qVal);
        potMode = (value.mode === 2) ? 2 : 1;
    } else {
        linearVal = getNum(value, linearVal);
        gainVal = getNum(rotValue, gainVal);
    }
    if (!rot2Enabled) potMode = 1; // no second mode configured → always mode 1

    // The active rotation (and its range/center) depends on the current mode.
    const activeRotMin = potMode === 2 ? rot2Min : rotMin;
    const activeRotMax = potMode === 2 ? rot2Max : rotMax;
    const currentRotVal = potMode === 2 ? qVal : gainVal;
    const capColorForMode = potMode === 2 ? capAccent2 : capAccent;

    // Center + detent for the ACTIVE range (middle-click recenters; drag snaps).
    const rotCenter = (activeRotMin + activeRotMax) / 2;
    const rotDetent = Math.max(0.5, (activeRotMax - activeRotMin) * 0.015);
    const snapRot = (v) => (Math.abs(v - rotCenter) <= rotDetent ? rotCenter : v);

    // Emit a full compound payload, patching only what changed.
    const emit = (patch) => {
        if (!onChange) return;
        onChange({
            value: patch.value !== undefined ? patch.value : linearVal,
            rotValue: patch.rotValue !== undefined ? patch.rotValue : gainVal,
            rotValue2: patch.rotValue2 !== undefined ? patch.rotValue2 : qVal,
            mode: patch.mode !== undefined ? patch.mode : potMode,
        });
    };
    // Set the active-mode rotation (and optionally the linear value) in one emit.
    const emitRot = (newActive, newLin) => {
        const p = {};
        if (newLin !== undefined) p.value = newLin;
        if (potMode === 2) p.rotValue2 = newActive; else p.rotValue = newActive;
        emit(p);
    };

    // -- Coordinate mapping ---------------------------------------------------
    const isLog = config?.logarithmic ?? fc?.logarithmic ?? (min > 0 && max > 0 && (max / min) >= 100);
    
    const valToNorm = (v) => {
        let clamped = Math.max(min, Math.min(max, v));
        if (isLog) {
            return Math.log10(clamped / min) / Math.log10(max / min);
        }
        return (clamped - min) / ((max - min) || 1);
    };

    const normToVal = (n) => {
        let clampedN = Math.max(0, Math.min(1, n));
        if (isLog) {
            return min * Math.pow(max / min, clampedN);
        }
        return min + (clampedN * (max - min));
    };

    const getHandlePos = (val) => {
        const norm = valToNorm(val);
        if (isHorizontal) {
            const drawW = width - 40;
            return 20 + drawW * norm;
        } else {
            const drawH = height - 40;
            return 20 + drawH * (1.0 - norm);
        }
    };
    const getValFromPos = (x, y) => {
        if (isHorizontal) {
            const drawW = width - 40;
            const norm = (x - 20) / drawW;
            return normToVal(norm);
        } else {
            const drawH = height - 40;
            const norm = (drawH - (y - 20)) / drawH;
            return normToVal(norm);
        }
    };

    // -- Rail + travelling cap render (canvas) --------------------------------
    const draw = (ctx) => {
        const cx = width / 2;
        const cy = height / 2;
        const isNarrow = isHorizontal ? height < 50 : width < 50;

        // Rotation is "active" (draw the long sweep line) when we're adjusting
        // the pot: pan-latch on, or dragging in a rotation-capable mode.
        const isAdjustingPot = panLatch || dragMode === 'rot' || dragMode === 'both';

        // Transparent background — let the panel/procedural backdrop show through.
        ctx.clearRect(0, 0, width, height);

        // Track
        ctx.strokeStyle = '#444';
        ctx.lineWidth = 4;
        ctx.lineCap = 'round';
        ctx.beginPath();
        if (isHorizontal) {
            ctx.moveTo(20, cy);
            ctx.lineTo(width - 20, cy);
        } else {
            ctx.moveTo(cx, 20);
            ctx.lineTo(cx, height - 20);
        }
        ctx.stroke();

        // Master fill (bottom → handle) or (left → handle)
        const handlePos = getHandlePos(linearVal);
        const isWbsElma = (kc?.knob_style === 'wbs-elma');
        ctx.strokeStyle = freestyle ? '#FF5555' : railColor;
        ctx.lineWidth = 4;
        ctx.beginPath();
        if (isHorizontal) {
            ctx.moveTo(20, cy);
            ctx.lineTo(handlePos, cy);
        } else {
            ctx.moveTo(cx, height - 20);
            ctx.lineTo(cx, handlePos);
        }
        ctx.stroke();

        // Tick scale
        const range = max - min;
        const steps = isNarrow ? 5 : 10;
        ctx.strokeStyle = '#666';
        ctx.lineWidth = 1;
        ctx.font = isNarrow ? '7px Arial' : '10px Arial';
        ctx.fillStyle = '#888';
        for (let i = 0; i <= steps; i++) {
            const norm = i / steps;
            const val = min + (norm * range);
            const tw = isNarrow ? 5 : 10;
            ctx.beginPath();
            if (isHorizontal) {
                const x = 20 + (width - 40) * norm;
                ctx.moveTo(x, cy - tw);
                ctx.lineTo(x, cy + tw);
                ctx.stroke();
                if (i % 2 === 0 && !isNarrow) {
                    ctx.textAlign = 'center';
                    ctx.fillText(val.toFixed(0), x, cy + 20);
                }
            } else {
                const y = 20 + (height - 40) * (1.0 - norm);
                ctx.moveTo(cx - tw, y);
                ctx.lineTo(cx + tw, y);
                ctx.stroke();
                if (i % 2 === 0 && !isNarrow) {
                    ctx.textAlign = 'left';
                    ctx.fillText(val.toFixed(0), cx + 15, y + 3);
                }
            }
        }

        const hx = isHorizontal ? handlePos : cx;
        const hy = isHorizontal ? cy : handlePos;

        // -- Travelling cap ---------------------------------------------------
        if (!isWbsElma) {
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
            ctx.arc(hx, hy, capRadius, 0, Math.PI * 2);
            ctx.fill();
            if (panLatch) ctx.restore();

            // Rotation indicator (mapped over the ACTIVE range: gain or Q)
            const rotRange = (activeRotMax - activeRotMin) || 200;
            const normalizedRot = ((currentRotVal - activeRotMin) / rotRange) * 2 - 1;
            const angle = normalizedRot * 135;
            const rad = (angle - 90) * Math.PI / 180;
            const drawLen = isAdjustingPot ? capRadius * 10 : capRadius;
            const px = hx + drawLen * Math.cos(rad);
            const py = hy + drawLen * Math.sin(rad);
            ctx.strokeStyle = capColorForMode;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(hx, hy);
            ctx.lineTo(px, py);
            ctx.stroke();

            // Center dot
            ctx.fillStyle = capColorForMode;
            ctx.beginPath();
            ctx.arc(hx, hy, 3, 0, Math.PI * 2);
            ctx.fill();
        } else {
            if (panLatch) {
                ctx.save();
                ctx.shadowColor = '#33A1FD';
                ctx.shadowBlur = 15;
                ctx.fillStyle = 'rgba(0,0,0,0)';
                ctx.beginPath();
                ctx.arc(hx, hy, capRadius, 0, Math.PI * 2);
                ctx.fill();
                ctx.restore();
            }
        }

        // -- Numerics ---------------------------------------------------------
        const isDragging = dragMode !== null;
        if (!isNarrow) {
            // Live value chip — shown whenever the readout is enabled OR the user is
            // actively moving the control, so you always see the value while dragging.
            if (showVal || isDragging) {
                const fTxt = linearVal >= 1000 ? `${(linearVal / 1000).toFixed(2)}k` : `${linearVal.toFixed(0)}`;
                const unit = showUnits && unitText ? unitText : 'Hz';
                const actTxt = potMode === 2 ? `Q ${currentRotVal.toFixed(2)}` : `${currentRotVal.toFixed(1)} dB`;
                const txt = `${fTxt} ${unit} · ${actTxt}`;
                ctx.font = 'bold 11px Arial';
                ctx.textAlign = 'center';
                const bx = isHorizontal ? hx : cx;
                const by = (isHorizontal ? cy : hy) - capRadius - 14;
                const tw = ctx.measureText(txt).width + 12;
                ctx.fillStyle = 'rgba(0,0,0,0.72)';
                ctx.fillRect(bx - tw / 2, by - 10, tw, 17);
                ctx.fillStyle = '#fff';
                ctx.fillText(txt, bx, by + 2);
            }
            if (freestyle) {
                ctx.textAlign = 'center';
                ctx.fillStyle = '#FF5555';
                ctx.font = 'bold 10px Arial';
                ctx.fillText('FREESTYLE', cx, isHorizontal ? height - 5 : height - 5);
            }
            // Dual-pot mode badge: shows which value the rotation is driving.
            if (rot2Enabled) {
                ctx.textAlign = 'center';
                ctx.font = 'bold 9px Arial';
                ctx.fillStyle = capColorForMode;
                ctx.fillText(potMode === 2 ? 'MODE 2 · Q' : 'MODE 1 · GAIN', cx, 10);
            }
        } else if (showVal) {
            ctx.fillStyle = '#000';
            ctx.textAlign = 'center';
            ctx.font = '7px Arial';
            ctx.fillText(`${linearVal.toFixed(0)}`, hx, hy + 3);
        }
    };

    React.useEffect(() => {
        if (canvasRef.current) {
            const ctx = canvasRef.current.getContext('2d');
            draw(ctx);
        }
    }, [linearVal, currentRotVal, width, height, railColor, dragMode, panLatch, freestyle, potMode]);

    // -- Interaction ----------------------------------------------------------
    const getPos = (e) => {
        const cv = canvasRef.current;
        const rect = cv.getBoundingClientRect();
        const sx = cv.width / (rect.width || 1);
        const sy = cv.height / (rect.height || 1);
        return { x: (e.clientX - rect.left) * sx, y: (e.clientY - rect.top) * sy };
    };
    const isOverHandle = (x, y) => {
        const hp = getHandlePos(linearVal);
        const hx = isHorizontal ? hp : width / 2;
        const hy = isHorizontal ? height / 2 : hp;
        const hit = capRadius * 1.5;   // generous hit area (touch-friendly)
        return Math.hypot(x - hx, y - hy) <= hit;
    };

    const handlePointerDown = (e) => {
        const { x, y } = getPos(e);
        // Middle button on the cap. Double middle-click → normalize (recenter the
        // active rotation). Single press → "free mode": a vertical fine-adjust drag
        // of the linear position (saves the start; up increments, down decrements).
        if (e.button === 1) {
            e.preventDefault();
            if (!isOverHandle(x, y)) return;
            const now = Date.now();
            const isDouble = (now - lastMiddleRef.current) <= midDoubleMs;
            lastMiddleRef.current = isDouble ? 0 : now;
            if (isDouble && midDoubleNormalizes) {
                emitRot(rotCenter);          // normalize
                dragRef.current.active = false;
                return;
            }
            try { canvasRef.current.setPointerCapture(e.pointerId); } catch (_) {}
            dragRef.current = { active: true, mode: 'middle', startX: x, startY: y, startLin: linearVal, startLinNorm: valToNorm(linearVal), startRot: currentRotVal, moved: false };
            setDragMode('linear');
            return;
        }
        try { canvasRef.current.setPointerCapture(e.pointerId); } catch (_) {}
        if (isOverHandle(x, y)) {
            const mode = freestyle ? 'both' : (panLatch || e.altKey ? 'rot' : 'linear');
            dragRef.current = { active: true, mode, startX: x, startY: y, startLin: linearVal, startLinNorm: valToNorm(linearVal), startRot: currentRotVal, isMod: e.altKey };
            setDragMode(mode);
        } else {
            // Bare rail: alt → snap to default, otherwise absolute-Y jump/drag.
            if (e.altKey) {
                emit({ value: defaultVal });
                return;
            }
            dragRef.current = { active: true, mode: 'rail', startX: x, startY: y, startLin: linearVal, startLinNorm: valToNorm(linearVal), startRot: currentRotVal, isMod: false };
            setDragMode('rail');
            const v = Math.max(min, Math.min(max, getValFromPos(x, y)));
            emit({ value: v });
        }
    };

    const handlePointerMove = (e) => {
        const d = dragRef.current;
        if (!d.active) return;
        const { x, y } = getPos(e);

        if (d.mode === 'rail') {
            const v = Math.max(min, Math.min(max, getValFromPos(x, y)));
            emit({ value: v });
            return;
        }

        // Middle-drag "free mode": fine vertical adjust of the POTENTIOMETER (the
        // active Gain/Q rotation) from the saved start — up = increment, down =
        // decrement, independent of fader orientation.
        if (d.mode === 'middle') {
            const dPix = d.startY - y;              // up is positive
            if (Math.abs(dPix) > 2) d.moved = true;
            const change = (dPix / midFine) * (activeRotMax - activeRotMin); // midFine px = full range
            const nextRot = snapRot(Math.max(activeRotMin, Math.min(activeRotMax, d.startRot + change)));
            emitRot(nextRot);
            return;
        }

        // Mid-drag mode switch when Alt is toggled (handle grab, non-freestyle).
        if (!freestyle && !panLatch) {
            const nowMod = e.altKey;
            if (nowMod !== d.isMod) {
                d.startX = x; d.startY = y; d.startLin = linearVal; d.startLinNorm = valToNorm(linearVal); d.startRot = currentRotVal;
                d.isMod = nowMod; d.mode = nowMod ? 'rot' : 'linear';
                setDragMode(d.mode);
            }
        }

        let nextLin = linearVal;
        let nextRot = currentRotVal;
        const rotActive = freestyle || d.mode === 'rot' || panLatch;
        const linActive = freestyle || (d.mode === 'linear' && !panLatch);

        if (rotActive) {
            const dRot = isHorizontal ? (d.startY - y) : (x - d.startX);
            // Scale sensitivity to the active range so gain (span ~64) and Q
            // (span ~10) feel the same under the pointer.
            let change = dRot * ((activeRotMax - activeRotMin) / 128);
            if (freestyle) change /= 2;
            nextRot = snapRot(Math.max(activeRotMin, Math.min(activeRotMax, d.startRot + change)));
        }
        if (linActive) {
            let normChange = 0;
            if (isHorizontal) {
                normChange = (x - d.startX) / (width - 40);
            } else {
                normChange = -(y - d.startY) / (height - 40);
            }
            if (freestyle) normChange /= 2;
            nextLin = Math.max(min, Math.min(max, normToVal(d.startLinNorm + normChange)));
        }
        emitRot(nextRot, nextLin);
    };

    const handlePointerUp = (e) => {
        // (Middle single-press = free-mode fine-adjust; normalize is on double-press.)
        dragRef.current.active = false;
        setDragMode(null);
        if (panLatch) setPanLatch(false);
        if (canvasRef.current) {
            try { canvasRef.current.releasePointerCapture(e.pointerId); } catch (_) {}
        }
    };

    const handleDoubleClick = (e) => {
        const { x, y } = getPos(e);
        if (!isOverHandle(x, y)) return;
        // Dual-pot: double-click toggles Mode 1 (gain) ↔ Mode 2 (Q). The cap flips
        // colour to signal which value the rotation now drives. Falls back to the
        // legacy pan-latch when no second mode is configured.
        if (rot2Enabled) emit({ mode: potMode === 2 ? 1 : 2 });
        else setPanLatch(true);
    };

    // Native, non-passive wheel so preventDefault works (fine-tune fader).
    React.useEffect(() => {
        const cv = canvasRef.current;
        if (!cv) return;
        const onWheel = (e) => {
            e.preventDefault();
            const delta = Math.sign(e.deltaY) * -1; // up is positive
            const wheelControlsPot = config?.fader_config?.wheel_controls_pot === true || config?.wheel_controls_pot === true;
            if (e.altKey || wheelControlsPot) {
                // Fine pot step scaled to the active range (Shift = 5× coarse);
                // snaps to center when it lands within the detent.
                const step = (e.shiftKey ? 5 : 1) * ((activeRotMax - activeRotMin) / 64);
                const nr = snapRot(Math.max(activeRotMin, Math.min(activeRotMax, currentRotVal + delta * step)));
                emitRot(nr);
            } else {
                const nl = Math.max(min, Math.min(max, linearVal + delta * ((max - min) / 50)));
                emit({ value: nl });
            }
        };
        cv.addEventListener('wheel', onWheel, { passive: false });
        return () => cv.removeEventListener('wheel', onWheel);
    }, [linearVal, currentRotVal, min, max]);

    return (
        <div ref={wrapperRef} className="ltp-wrapper" style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            position: 'relative',
            width: typeof cfgWidth === 'string' ? cfgWidth : `${cfgWidth}px`,
            height: typeof cfgHeight === 'string' ? cfgHeight : `${cfgHeight}px`,
            justifyContent: 'center'
        }}>
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
                        backgroundColor: 'transparent',
                        touchAction: 'none',
                        display: 'block',
                    }}
                />
                {(kc?.knob_style === 'wbs-elma') && window.KnobCapWBSElma && (
                    <svg style={{
                        position: 'absolute',
                        left: (isHorizontal ? getHandlePos(linearVal) : width / 2) - capRadius,
                        top: (isHorizontal ? height / 2 : getHandlePos(linearVal)) - capRadius,
                        width: capRadius * 2,
                        height: capRadius * 2,
                        pointerEvents: 'none',
                        overflow: 'visible'
                    }}>
                        <window.KnobCapWBSElma 
                            filterId={`ltpfader-${(config?.topic || Math.random().toString(36)).replace(/\W/g, '_')}`}
                            center={capRadius}
                            radius={capRadius}
                            angle={-(((currentRotVal - activeRotMin) / ((activeRotMax - activeRotMin) || 200)) * 2 - 1) * 135 + 90}
                            config={{
                                cosmetics: {
                                    styling: {
                                        fill_color: "#546E7A",
                                        cap_color: capColorForMode,
                                        outline_color: "#000",
                                        outline_thickness: 1
                                    },
                                    flutes: 18,
                                    cap: { show: true, color: capColorForMode },
                                    wing: { show: false },
                                    pointer_tip: { show: true, color: "#546E7A", length: 0.2 },
                                    line: { color: config?.cosmetics?.line?.color || "#ffffff" }
                                }
                            }}
                        />
                    </svg>
                )}
            </div>
        </div>
    );
};

window.LTPFader = LTPFader;
