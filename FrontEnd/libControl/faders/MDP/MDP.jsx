/**
 * Header: MDP.jsx
 * Purpose: MDP component or utility.
 * Description: Handles logic and rendering for MDP component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

/**
 * MDP - Multi Dimensional Panner Component
 * Author: Anthony Peter Kuzub / Gemini (Collaborator)
 * Version: 20260506.1900.1
 *
 * Description: Multi-axis controller (X, Y, Linear, Rotation) with free placement.
 * Based on the perfect reference at oaGuiElements/Core/special/composite_mdp/index.html
 */

// Inline comment: Logic for MDP
const MDP = ({ config, value, onChange }) => {
    const canvasRef = React.useRef(null);
    const containerRef = React.useRef(null);

    // --- 1. State Extraction & Robust Defaults ---
    const c = config || {};
    const ltpCfg = c.ltp || {};
    const graphCfg = c.graph || {};
    const [lang] = window.useMqttLang ? window.useMqttLang() : ['En'];

    const xlim = graphCfg.xlim || [0, 100];
    const ylim = graphCfg.ylim || [0, 100];
    const minLtp = ltpCfg.min !== undefined ? ltpCfg.min : 0;
    const maxLtp = ltpCfg.max !== undefined ? ltpCfg.max : 100;

    // Composite State: { x, y, angle, value, rotValue }
    const defaultState = {
        x: c.initial_x || (xlim[0] + xlim[1]) / 2,
        y: c.initial_y || (ylim[0] + ylim[1]) / 2,
        angle: 0,
        value: ltpCfg.value_default || (minLtp + maxLtp) / 2,
        rotValue: 0
    };

    const s = (typeof value === 'object' && value !== null) ? { ...defaultState, ...value } : defaultState;

    // --- 2. Interaction State ---
    const [isHovered, setIsHovered] = React.useState(false);
    const [isWidgetSelected, setIsWidgetSelected] = React.useState(false);
    const [isRotaryActive, setIsRotaryActive] = React.useState(false);
    
    // Map: TouchID -> { x, y, role, startX, startY, startState }
    const touchesRef = React.useRef(new Map());
    const longPressTimerRef = React.useRef(null);

    // --- 3. Coordinate Helpers ---
    const getCanvasPos = (faderX, faderY, w, h) => {
        const px = ((faderX - xlim[0]) / (xlim[1] - xlim[0])) * w;
        const py = h - ((faderY - ylim[0]) / (ylim[1] - ylim[0])) * h;
        return { x: px, y: py };
    };

    const getFaderPos = (canvasX, canvasY, w, h) => {
        const fx = (canvasX / w) * (xlim[1] - xlim[0]) + xlim[0];
        const fy = ((h - canvasY) / h) * (ylim[1] - ylim[0]) + ylim[0];
        return { x: fx, y: fy };
    };

    const rotatePoint = (px, py, cx, cy, angleDeg) => {
        const rad = angleDeg * (Math.PI / 180);
        const cos = Math.cos(rad);
        const sin = Math.sin(rad);
        const nx = cos * (px - cx) - sin * (py - cy) + cx;
        const ny = sin * (px - cx) + cos * (py - cy) + cy;
        return { x: nx, y: ny };
    };

    const getCapCanvasPos = (faderX, faderY, angle, val, trackLen, w, h) => {
        const base = getCanvasPos(faderX, faderY, w, h);
        const norm = (val - minLtp) / (maxLtp - minLtp || 1);
        const localY = (trackLen / 2) - (norm * trackLen);
        return rotatePoint(base.x, base.y + localY, base.x, base.y, angle);
    };

    // --- 4. Rendering ---
    const draw = (ctx, w, h) => {
        ctx.clearRect(0, 0, w, h);

        const trackLen = 150;
        const capRadius = 20;
        const pos = getCanvasPos(s.x, s.y, w, h);
        const ang = s.angle;

        // A. Background Grid (from reference)
        if (graphCfg.show_grid) {
            ctx.strokeStyle = graphCfg.style?.grid_color || "#333";
            ctx.lineWidth = 1;
            for (let i = 1; i < 10; i++) {
                const lx = (i / 10) * w;
                const ly = (i / 10) * h;
                ctx.beginPath(); ctx.moveTo(lx, 0); ctx.lineTo(lx, h); ctx.stroke();
                ctx.beginPath(); ctx.moveTo(0, ly); ctx.lineTo(w, ly); ctx.stroke();
            }
        }

        // B. Widget Move Highlight
        if (isWidgetSelected) {
            ctx.save();
            ctx.translate(pos.x, pos.y);
            ctx.rotate(ang * Math.PI / 180);
            ctx.fillStyle = "rgba(244, 144, 44, 0.2)";
            ctx.fillRect(-30, -trackLen/2 - 15, 60, trackLen + 30);
            ctx.restore();
        }

        // C. Track
        const t1 = rotatePoint(pos.x, pos.y - trackLen/2, pos.x, pos.y, ang);
        const t2 = rotatePoint(pos.x, pos.y + trackLen/2, pos.x, pos.y, ang);
        
        ctx.beginPath();
        ctx.moveTo(t1.x, t1.y); ctx.lineTo(t2.x, t2.y);
        ctx.lineWidth = 6; ctx.lineCap = "round"; ctx.strokeStyle = "#000"; ctx.stroke();
        ctx.lineWidth = 2; ctx.strokeStyle = "#444"; ctx.stroke();

        // D. Ticks
        ctx.beginPath(); ctx.lineWidth = 1; ctx.strokeStyle = "#666";
        for (let i = 0; i <= 10; i++) {
            const ly = (trackLen/2) - (trackLen * (i/10));
            const side = (i % 5 === 0) ? 12 : 6;
            const pt1 = rotatePoint(pos.x - 10, pos.y + ly, pos.x, pos.y, ang);
            const pt2 = rotatePoint(pos.x - 10 - side, pos.y + ly, pos.x, pos.y, ang);
            ctx.moveTo(pt1.x, pt1.y); ctx.lineTo(pt2.x, pt2.y);
            
            const pt3 = rotatePoint(pos.x + 10, pos.y + ly, pos.x, pos.y, ang);
            const pt4 = rotatePoint(pos.x + 10 + side, pos.y + ly, pos.x, pos.y, ang);
            ctx.moveTo(pt3.x, pt3.y); ctx.lineTo(pt4.x, pt4.y);
        }
        ctx.stroke();

        // E. Cap
        const cap = getCapCanvasPos(s.x, s.y, ang, s.value, trackLen, w, h);
        const accent = "#f4902c";

        ctx.beginPath();
        ctx.arc(cap.x, cap.y, capRadius, 0, Math.PI * 2);
        ctx.fillStyle = "#333"; ctx.fill();
        ctx.lineWidth = 2; ctx.strokeStyle = isHovered ? accent : "#888"; ctx.stroke();

        // F. Intensity Arc
        const startDeg = 135; 
        const sweepDeg = ((s.rotValue + 130) / 260) * 270;
        ctx.beginPath();
        ctx.arc(cap.x, cap.y, capRadius - 5, startDeg * Math.PI / 180, (startDeg + sweepDeg) * Math.PI / 180);
        ctx.strokeStyle = accent; ctx.lineWidth = 4; ctx.stroke();

        // G. Pointer
        const ptrAngle = (-90 + s.rotValue) * (Math.PI / 180);
        const ptrLen = isRotaryActive ? (capRadius * 10) : (capRadius - 2);
        ctx.beginPath();
        ctx.moveTo(cap.x, cap.y);
        ctx.lineTo(cap.x + ptrLen * Math.cos(ptrAngle), cap.y + ptrLen * Math.sin(ptrAngle));
        ctx.strokeStyle = accent; ctx.lineWidth = 3; ctx.stroke();
        
        ctx.beginPath(); ctx.arc(cap.x, cap.y, 3, 0, Math.PI * 2);
        ctx.fillStyle = accent; ctx.fill();

        // H. Value Text
        ctx.font = "bold 10px monospace"; ctx.textAlign = "center";
        ctx.fillStyle = "#fff";
        ctx.fillText(s.value.toFixed(1), cap.x, cap.y - capRadius - 15);
        ctx.fillStyle = "#aaa";
        ctx.fillText(`R:${s.rotValue.toFixed(0)}`, cap.x, cap.y + capRadius + 15);
    };

    React.useEffect(() => {
        if (canvasRef.current) {
            const ctx = canvasRef.current.getContext('2d');
            const w = canvasRef.current.width;
            const h = canvasRef.current.height;
            draw(ctx, w, h);
        }
    }, [s, isHovered, isWidgetSelected, isRotaryActive]);

    // --- 5. Interaction Logics ---
    const handleStart = (e) => {
        const rect = canvasRef.current.getBoundingClientRect();
        const pts = e.touches ? Array.from(e.touches).map(t => ({ id: t.identifier, x: t.clientX - rect.left, y: t.clientY - rect.top })) 
                               : [{ id: 'mouse', x: e.clientX - rect.left, y: e.clientY - rect.top }];

        for (const pt of pts) {
            const trackLen = 150;
            const capPos = getCapCanvasPos(s.x, s.y, s.angle, s.value, trackLen, canvasRef.current.width, canvasRef.current.height);
            const dist = Math.sqrt((pt.x - capPos.x)**2 + (pt.y - capPos.y)**2);

            // Cap Hit
            if (dist < 30) {
                // Check if secondary finger on existing cap hold
                let primary = null;
                for (const [tid, t] of touchesRef.current) {
                    if (t.role === 'cap_primary') primary = t;
                }

                if (primary) {
                    touchesRef.current.set(pt.id, { role: 'cap_rotary', startX: pt.x, startRot: s.rotValue });
                    setIsRotaryActive(true);
                } else {
                    touchesRef.current.set(pt.id, { role: 'cap_primary', startY: pt.y, startVal: s.value });
                }
                continue;
            }

            // Body Hit (Check move timer)
            const basePos = getCanvasPos(s.x, s.y, canvasRef.current.width, canvasRef.current.height);
            const local = rotatePoint(pt.x, pt.y, basePos.x, basePos.y, -s.angle);
            if (Math.abs(local.x - basePos.x) < 30 && Math.abs(local.y - basePos.y) < trackLen/2 + 20) {
                const timer = setTimeout(() => {
                    setIsWidgetSelected(true);
                    const t = touchesRef.current.get(pt.id);
                    if (t) t.role = 'widget_move';
                }, 1000);
                touchesRef.current.set(pt.id, { role: 'widget_wait', timer, startX: pt.x, startY: pt.y, startAngle: s.angle });
            }
        }
    };

    const handleMove = (e) => {
        const rect = canvasRef.current.getBoundingClientRect();
        const pts = e.touches ? Array.from(e.touches).map(t => ({ id: t.identifier, x: t.clientX - rect.left, y: t.clientY - rect.top })) 
                               : [{ id: 'mouse', x: e.clientX - rect.left, y: e.clientY - rect.top }];

        let next = { ...s };
        let changed = false;

        for (const pt of pts) {
            const t = touchesRef.current.get(pt.id);
            if (!t) continue;

            if (t.role === 'widget_wait') {
                const d = Math.sqrt((pt.x - t.startX)**2 + (pt.y - t.startY)**2);
                if (d > 10) { clearTimeout(t.timer); touchesRef.current.delete(pt.id); }
            } else if (t.role === 'widget_move') {
                // Check if multiple fingers moving widget (Rotate)
                const movers = Array.from(touchesRef.current.values()).filter(x => x.role === 'widget_move');
                if (movers.length >= 2) {
                    // Simpler relative rotation for prototype
                    const dx = pt.x - t.startX;
                    next.angle = t.startAngle + dx;
                } else {
                    const fp = getFaderPos(pt.x, pt.y, canvasRef.current.width, canvasRef.current.height);
                    next.x = Math.max(xlim[0], Math.min(xlim[1], fp.x));
                    next.y = Math.max(ylim[0], Math.min(ylim[1], fp.y));
                }
                changed = true;
            } else if (t.role === 'cap_primary') {
                const dy = t.startY - pt.y;
                const trackLen = 150;
                const delta = (dy / trackLen) * (maxLtp - minLtp);
                next.value = Math.max(minLtp, Math.min(maxLtp, t.startVal + delta));
                changed = true;
            } else if (t.role === 'cap_rotary') {
                const dx = pt.x - t.startX;
                next.rotValue = Math.max(-130, Math.min(130, t.startRot + dx));
                changed = true;
            }
        }

        if (changed) onChange(next);
    };

    const handleEnd = (e) => {
        const changed = e.changedTouches ? Array.from(e.changedTouches).map(t => t.identifier) : ['mouse'];
        for (const tid of changed) {
            const t = touchesRef.current.get(tid);
            if (t) {
                if (t.timer) clearTimeout(t.timer);
                if (t.role === 'widget_move') setIsWidgetSelected(false);
                if (t.role === 'cap_rotary') setIsRotaryActive(false);
                touchesRef.current.delete(tid);
            }
        }
    };

    const layoutW = config?.layout?.width || 500;
    const layoutH = config?.layout?.height || 500;

    return (
        <div ref={containerRef} className="mdp-container" style={{ 
            background: (window.OaTransparency ? window.OaTransparency.bg(config, '#111') : '#111'), border: '1px solid #333', borderRadius: '4px',
            padding: '10px', boxShadow: 'inset 0 2px 10px rgba(0,0,0,0.5)'
        }}>
            <div style={{ color: '#aaa', fontSize: '11px', fontWeight: 'bold', marginBottom: '10px', textAlign: 'center' }}>
                {(c.label_active?.[lang] || c.label?.[lang] || "MDP").toUpperCase()}
            </div>
            <canvas
                ref={canvasRef}
                width={layoutW} height={layoutH}
                onPointerDown={handleStart}
                onPointerMove={handleMove}
                onPointerUp={handleEnd}
                onPointerLeave={handleEnd}
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
                style={{ display: 'block', touchAction: 'none', cursor: 'crosshair', borderRadius: '2px', background: '#000' }}
            />
        </div>
    );
};

window.MDP = MDP;
