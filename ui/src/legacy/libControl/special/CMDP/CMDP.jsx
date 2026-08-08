import { CMDPEditor } from './CMDPEditor.jsx'

/**
 * Header: CMDP.jsx
 * Purpose: CMDP component or utility.
 * Description: Handles logic and rendering for CMDP component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// CMDP - Circular Motion Displacement Potentiometer Component
// Author: Gemini (Collaborator)
// Version: 20260701.1200.2
//
// Description: Polar-coordinate multi-channel panner/fader. Renders every
// channel from config.channels[] arranged by angle around a circle, colored
// by its group (config.group_configs[]). Rendering + interaction ported from
// the standalone CMDP demo (better track/tick/knob drawing, segment-distance
// hit testing, hover label read-out, per-channel drag ballistics).

// Inline comment: Logic for CMDP
const CMDP = ({ config, value, onChange, size }) => {
    const canvasRef = React.useRef(null);

    // --- Geometry -----------------------------------------------------------
    const CANVAS = 1400;                 // internal resolution (scaled by CSS)
    const NEAR_RADIUS = 120;
    const FAR_RADIUS = 380;
    const trackLen = FAR_RADIUS - NEAR_RADIUS;

    // --- Robust value helpers ----------------------------------------------
    const num = (v, d) => { const n = typeof v === 'number' ? v : parseFloat(v); return Number.isFinite(n) ? n : d; };
    const clamp = (v) => Math.max(0, Math.min(100, v));

    // distToSegment: perpendicular distance from a point to a line segment
    // (ported from the demo — enables clean radial hit-testing of each fader).
    const distToSegment = (px, py, x1, y1, x2, y2) => {
        const l2 = (x1 - x2) ** 2 + (y1 - y2) ** 2;
        if (l2 === 0) return Math.hypot(px - x1, py - y1);
        const t = Math.max(0, Math.min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / l2));
        return Math.hypot(px - (x1 + t * (x2 - x1)), py - (y1 + t * (y2 - y1)));
    };

    // --- Mutable interaction state (refs so drags don't thrash React) -------
    const fadersRef = React.useRef([]);
    const activeRef = React.useRef(null);
    const hoveredRef = React.useRef(null);
    const dragRef = React.useRef({ startX: 0, startY: 0, startVal: 0, startRot: 0, startAngle: 0 });
    const handlersRef = React.useRef({});

    // --- Build the fader models from config (channels + group_configs) ------
    const buildFaders = () => {
        const chans = (value && value.channels) || config?.channels || config?.nodeJson?.channels || [];
        const grps = (value && value.group_configs) || config?.group_configs || config?.nodeJson?.group_configs || [];
        const byName = {};
        grps.forEach((g, i) => { byName[g.name] = { color: g.color, index: i, visible: g.visible !== false, mute: !!g.mute }; });
        const fallback = config?.color || '#f4902c';
        return (Array.isArray(chans) ? chans : []).map((ch, idx) => {
            const g = byName[ch.group] || { color: fallback, index: 0, visible: true, mute: false };
            return {
                id: ch.id !== undefined ? ch.id : idx,
                label: ch.name || String(ch.id ?? idx),
                angle: num(ch.angle, 0),
                valCurrent: clamp(num(ch.depth, 50)),   // depth: Near=0 -> Far=100
                rotCurrent: clamp(num(ch.level, 70)),    // level: knob intensity
                color: g.color || fallback,
                groupIndex: g.index,
                groupVisible: g.visible,
                chanVisible: ch.visible !== false,
                mute: !!ch.mute || g.mute,
                hovered: false,
                dragging: false,
                _src: ch,
            };
        });
    };

    const isVisible = (f) => f.groupVisible && f.chanVisible;

    // --- Hit testing (segment distance along the fader's radial track) ------
    const hitTest = (f, mx, my, cx, cy) => {
        const rad = f.angle * Math.PI / 180;
        const x1 = cx + (NEAR_RADIUS - 20) * Math.cos(rad);
        const y1 = cy + (NEAR_RADIUS - 20) * Math.sin(rad);
        const x2 = cx + (FAR_RADIUS + 20) * Math.cos(rad);
        const y2 = cy + (FAR_RADIUS + 20) * Math.sin(rad);
        return distToSegment(mx, my, x1, y1, x2, y2) < 30;
    };

    const getTopFaderAt = (mx, my, cx, cy) => {
        const faders = fadersRef.current;
        for (let i = faders.length - 1; i >= 0; i--) {
            const f = faders[i];
            if (isVisible(f) && hitTest(f, mx, my, cx, cy)) return f;
        }
        return null;
    };

    // --- Center hub face: shows the hovered/active channel name -------------
    const drawFace = (ctx, cx, cy) => {
        const r = 40;
        const orange = config?.color || '#f4902c';
        ctx.save();
        ctx.translate(cx, cy);
        ctx.fillStyle = '#333'; ctx.strokeStyle = orange; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.ellipse(-r - 5, 0, 10, 15, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
        ctx.beginPath(); ctx.ellipse(r + 5, 0, 10, 15, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
        ctx.fillStyle = '#444'; ctx.strokeStyle = orange;
        ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
        const target = activeRef.current || hoveredRef.current;
        if (target) {
            ctx.fillStyle = 'white'; ctx.font = 'bold 10px Arial'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
            let txt = target.label || '';
            if (txt.length > 10) txt = txt.substring(0, 8) + '..';
            ctx.fillText(txt, 0, 0);
        }
        ctx.fillStyle = orange;
        ctx.beginPath(); ctx.moveTo(0, -r + 5 - 15); ctx.lineTo(-10, -r + 5); ctx.lineTo(10, -r + 5); ctx.closePath(); ctx.fill(); ctx.stroke();
        ctx.restore();
    };

    // --- One channel: track, ticks, knob cap, sweep, pointer, label ---------
    const renderFader = (ctx, f, cx, cy) => {
        const rad = f.angle * Math.PI / 180;
        const dist = NEAR_RADIUS + (trackLen / 2);
        const fx = cx + dist * Math.cos(rad);
        const fy = cy + dist * Math.sin(rad);

        ctx.save();
        ctx.globalAlpha = f.mute ? 0.35 : 1;
        ctx.translate(fx, fy);
        ctx.rotate((f.angle + 90) * Math.PI / 180);

        const tl = trackLen;
        ctx.lineCap = 'round';
        ctx.lineWidth = 6; ctx.strokeStyle = '#000'; ctx.beginPath(); ctx.moveTo(0, -tl / 2); ctx.lineTo(0, tl / 2); ctx.stroke();
        ctx.lineWidth = 2; ctx.strokeStyle = '#222'; ctx.beginPath(); ctx.moveTo(0, -tl / 2); ctx.lineTo(0, tl / 2); ctx.stroke();

        // Scale ticks (long every 5th)
        ctx.lineWidth = 1; ctx.strokeStyle = '#666';
        for (let i = 0; i <= 10; i++) {
            const ly = (-tl / 2) + (tl * (i / 10));
            const len = (i % 5 === 0) ? 10 : 5;
            ctx.beginPath(); ctx.moveTo(-15, ly); ctx.lineTo(-15 - len, ly); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(15, ly); ctx.lineTo(15 + len, ly); ctx.stroke();
        }

        // Knob cap at the depth position
        const norm = f.valCurrent / 100;
        const capY = (-tl / 2) + (norm * tl);
        ctx.translate(0, capY);
        ctx.rotate(-((f.angle + 90) * Math.PI / 180));

        const r = 22;
        ctx.fillStyle = '#333';
        ctx.strokeStyle = (f.hovered || f.dragging) ? '#fff' : f.color;
        ctx.lineWidth = (f.hovered || f.dragging) ? 3 : 2;
        ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.fill(); ctx.stroke();

        // Intensity sweep arc + pointer
        const startDeg = 135;
        const currentDeg = 135 + (f.rotCurrent / 100) * 270;
        const ar = r - 5;
        ctx.strokeStyle = f.color; ctx.lineWidth = 4;
        ctx.beginPath(); ctx.arc(0, 0, ar, startDeg * Math.PI / 180, currentDeg * Math.PI / 180); ctx.stroke();

        const indRad = currentDeg * (Math.PI / 180);
        ctx.lineWidth = 3;
        ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo((r - 2) * Math.cos(indRad), (r - 2) * Math.sin(indRad)); ctx.stroke();
        ctx.beginPath(); ctx.arc(0, 0, 3, 0, Math.PI * 2); ctx.fillStyle = f.color; ctx.fill();

        ctx.font = '10px Arial'; ctx.fillStyle = '#fff'; ctx.textAlign = 'center';
        ctx.fillText(f.valCurrent.toFixed(1), 0, -30);
        ctx.fillStyle = '#aaa'; ctx.font = '9px Arial'; ctx.fillText(f.rotCurrent.toFixed(0), 0, 35);
        ctx.restore();

        // Perimeter label — staggered per group, lifts out when active, flipped
        // so it stays upright on the left half of the circle.
        ctx.save();
        ctx.globalAlpha = f.mute ? 0.35 : 1;
        const isActive = f.dragging || f.hovered;
        const groupOffset = f.groupIndex * 30;
        const activeOffset = isActive ? 20 : 0;
        const labDist = FAR_RADIUS + 35 + groupOffset + activeOffset;
        const lx = cx + labDist * Math.cos(rad);
        const ly = cy + labDist * Math.sin(rad);
        ctx.translate(lx, ly);
        let textRot = (f.angle + 90) * Math.PI / 180;
        let checkAngle = (f.angle + 90) % 360;
        if (checkAngle < 0) checkAngle += 360;
        if (checkAngle > 90 && checkAngle < 270) textRot += Math.PI;
        ctx.rotate(textRot);
        ctx.fillStyle = f.color; ctx.font = 'bold 12px Arial'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText(f.label, 0, 0);
        ctx.restore();
    };

    // --- Full scene ---------------------------------------------------------
    const draw = (ctx, w, h) => {
        const cx = w / 2;
        const cy = h / 2;

        ctx.fillStyle = '#222';
        ctx.fillRect(0, 0, w, h);

        drawFace(ctx, cx, cy);

        // Near/Far guide rings
        ctx.strokeStyle = '#f4902c';
        ctx.setLineDash([5, 5]);
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(cx, cy, NEAR_RADIUS, 0, Math.PI * 2); ctx.stroke();
        ctx.beginPath(); ctx.arc(cx, cy, FAR_RADIUS, 0, Math.PI * 2); ctx.stroke();
        ctx.setLineDash([]);

        ctx.fillStyle = '#f4902c'; ctx.font = 'bold 12px Arial'; ctx.textAlign = 'center';
        ctx.fillText('NEAR', cx, cy - NEAR_RADIUS - 10);
        ctx.fillText('FAR', cx, cy - FAR_RADIUS - 10);

        fadersRef.current.forEach(f => { if (isVisible(f)) renderFader(ctx, f, cx, cy); });
    };

    const drawNow = () => {
        const cv = canvasRef.current;
        if (!cv) return;
        draw(cv.getContext('2d'), cv.width, cv.height);
    };

    // --- Publish updated channels back through onChange ---------------------
    const publish = () => {
        if (!onChange) return;
        const channels = fadersRef.current.map(f => ({
            ...f._src,
            angle: f.angle,
            level: f.rotCurrent,
            depth: f.valCurrent,
        }));
        // Preserve the current group config in the shared value so a CMDP drag
        // never drops group edits made by a companion CMDPEditor.
        const group_configs = (value && value.group_configs)
            || config?.group_configs || config?.nodeJson?.group_configs || [];
        onChange({ channels, group_configs });
    };

    // --- Pointer coords in internal canvas space (handles CSS scaling) ------
    const getPos = (e) => {
        const cv = canvasRef.current;
        const rect = cv.getBoundingClientRect();
        const sx = cv.width / rect.width;
        const sy = cv.height / rect.height;
        return { mx: (e.clientX - rect.left) * sx, my: (e.clientY - rect.top) * sy, cx: cv.width / 2, cy: cv.height / 2 };
    };

    const handlePointerDown = (e) => {
        const { mx, my, cx, cy } = getPos(e);
        const hit = getTopFaderAt(mx, my, cx, cy);
        if (hit) {
            activeRef.current = hit;
            hit.dragging = true;
            dragRef.current = { startX: mx, startY: my, startVal: hit.valCurrent, startRot: hit.rotCurrent, startAngle: hit.angle };
            canvasRef.current.setPointerCapture(e.pointerId);
            drawNow();
        }
    };

    const handlePointerMove = (e) => {
        const { mx, my, cx, cy } = getPos(e);
        const f = activeRef.current;

        if (!f) {
            // Hover tracking
            const hit = getTopFaderAt(mx, my, cx, cy);
            let changed = false;
            fadersRef.current.forEach(fd => { const h = fd === hit; if (fd.hovered !== h) { fd.hovered = h; changed = true; } });
            if (hoveredRef.current !== hit) { hoveredRef.current = hit; changed = true; }
            if (canvasRef.current) canvasRef.current.style.cursor = hit ? 'pointer' : 'default';
            if (changed) drawNow();
            return;
        }

        const d = dragRef.current;
        const isAlt = e.altKey;
        const isRight = e.buttons === 2;
        const isMiddle = e.buttons === 4;
        const isLeft = e.buttons === 1;

        if ((isAlt && isLeft) || isMiddle) {
            // Azimuth (angle)
            const dx = mx - cx, dy = my - cy;
            f.angle = Math.atan2(dy, dx) * 180 / Math.PI;
        } else if (isRight) {
            // Intensity (knob sweep)
            const dx = mx - d.startX;
            f.rotCurrent = clamp(d.startRot + dx * 0.5);
        } else if (isLeft) {
            // Depth: project drag onto the radial vector (out = decrease)
            const rad = f.angle * Math.PI / 180;
            const dx = mx - d.startX;
            const dy = my - d.startY;
            const proj = dx * Math.cos(rad) + dy * Math.sin(rad);
            const change = -(proj / trackLen) * 100;
            f.valCurrent = clamp(d.startVal + change);
        }
        publish();
        drawNow();
    };

    const handlePointerUp = (e) => {
        if (activeRef.current) { activeRef.current.dragging = false; activeRef.current = null; }
        if (canvasRef.current) {
            try { canvasRef.current.releasePointerCapture(e.pointerId); } catch (_) {}
        }
        drawNow();
    };

    // Wheel: intensity, or angle with ctrl/alt (native non-passive listener).
    const handleWheel = (e) => {
        e.preventDefault();
        const { mx, my, cx, cy } = getPos(e);
        const target = hoveredRef.current || getTopFaderAt(mx, my, cx, cy);
        if (!target) return;
        const step = Math.sign(e.deltaY) * -1;
        if (e.altKey || e.ctrlKey) {
            target.angle += step * 3;
        } else {
            target.rotCurrent = clamp(target.rotCurrent + step * 5);
        }
        publish();
        drawNow();
    };

    // Keep latest handlers reachable from the once-bound native wheel listener.
    handlersRef.current.wheel = handleWheel;

    // Rebuild models when the node/data changes — including external edits to the
    // shared value (e.g. from a companion CMDPEditor). Skip while a drag is in
    // progress so we don't clobber the fader the user is holding.
    const valueSig = React.useMemo(
        () => { try { return JSON.stringify({ c: value?.channels, g: value?.group_configs }); } catch (_) { return ''; } },
        [value]
    );
    React.useEffect(() => {
        if (activeRef.current) return; // don't rebuild mid-drag
        fadersRef.current = buildFaders();
        hoveredRef.current = null;
        drawNow();
        // Seed the shared topic once (from config data) so a companion CMDPEditor
        // on the same topic has channels/groups to edit before any drag happens.
        if (onChange && !(value && value.channels)) publish();
        // eslint-disable-next-line
    }, [config?.path, valueSig, (config?.channels || config?.nodeJson?.channels || []).length, (config?.group_configs || config?.nodeJson?.group_configs || []).length]);

    // Native wheel listener (passive:false so preventDefault works).
    React.useEffect(() => {
        const cv = canvasRef.current;
        if (!cv) return;
        const onWheel = (e) => { if (handlersRef.current.wheel) handlersRef.current.wheel(e); };
        cv.addEventListener('wheel', onWheel, { passive: false });
        return () => cv.removeEventListener('wheel', onWheel);
    }, []);

    // Grouping/editing overlay (CMDPEditor) laid over the canvas, top-right —
    // like the demo's group/status panels. Toggled with the ☰ button.
    const [showEditor, setShowEditor] = React.useState(false);
    const accent = config?.color || '#f4902c';

    return (
        <div style={{ position: 'relative', width: '100%', maxWidth: '900px', margin: '0 auto' }}>
            <canvas
                ref={canvasRef}
                width={CANVAS}
                height={CANVAS}
                onPointerDown={handlePointerDown}
                onPointerMove={handlePointerMove}
                onPointerUp={handlePointerUp}
                onContextMenu={e => e.preventDefault()}
                style={{
                    display: 'block',
                    width: '100%',
                    height: 'auto',
                    aspectRatio: '1 / 1',
                    cursor: 'default',
                    touchAction: 'none',
                }}
            />
            <button
                onClick={() => setShowEditor(s => !s)}
                title={showEditor ? 'Hide editor' : 'Groups & channels editor'}
                style={{
                    position: 'absolute', top: '8px', right: '8px', zIndex: 20,
                    background: showEditor ? accent : 'rgba(28,28,30,0.9)',
                    color: showEditor ? '#000' : accent, border: `1px solid ${accent}`,
                    borderRadius: '5px', width: '30px', height: '30px', cursor: 'pointer',
                    fontSize: '15px', lineHeight: '28px', padding: 0, fontWeight: 'bold',
                }}
            >{showEditor ? '✕' : '☰'}</button>
            {showEditor && CMDPEditor && (
                <div style={{ position: 'absolute', top: '44px', right: '8px', width: '280px', maxWidth: '80%', maxHeight: 'calc(100% - 56px)', zIndex: 15 }}>
                    <CMDPEditor config={config} value={value} onChange={onChange} />
                </div>
            )}
        </div>
    );
};

window.CMDP = CMDP;

export { CMDP }
