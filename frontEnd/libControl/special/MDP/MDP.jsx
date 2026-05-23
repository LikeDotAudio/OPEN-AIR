/**
 * MDP - Multi-Dimensional Panner Component
 * Author: Anthony Peter Kuzub / Gemini (Collaborator)
 * Version: 20260507.1200.1
 *
 * Description: Advanced multi-axis panner with widget rotation and free move.
 * Robust numeric extraction for MQTT composite states.
 */

const MDP = ({ config, value, rotValue, angle, onChange }) => {
    const canvasRef = React.useRef(null);
    const [isHovered, setIsHovered] = React.useState(false);
    const [draggingRole, setDraggingRole] = React.useState(null); // 'cap', 'widget_move'
    const [interactionState, setInteractionState] = React.useState({});

    const valMin = 0; const valMax = 100;
    const rotMin = -130; const rotMax = 130;
    const trackLen = config?.trackLen || 200;
    const capRadius = 22;

    // --- Robust Value Extraction ---
    const getNum = (v, fallback) => (typeof v === 'number' ? v : (typeof v === 'string' ? parseFloat(v) : fallback));
    
    let valCurrent = (valMin + valMax) / 2;
    let rotCurrent = 0;
    let widgetAngle = angle !== undefined ? getNum(angle, 0) : getNum(config?.angle, 0);
    let x = config?.x || 150;
    let y = config?.y || 150;

    if (value && typeof value === 'object' && !Array.isArray(value)) {
        valCurrent = getNum(value.value, valCurrent);
        rotCurrent = getNum(value.rotValue, rotCurrent);
        if (value.angle !== undefined) widgetAngle = getNum(value.angle, widgetAngle);
        if (value.x !== undefined) x = getNum(value.x, x);
        if (value.y !== undefined) y = getNum(value.y, y);
    } else {
        valCurrent = getNum(value, valCurrent);
        rotCurrent = getNum(rotValue, rotCurrent);
    }

    const rotatePoint = (px, py, cx, cy, angleDeg) => {
        const rad = angleDeg * (Math.PI / 180);
        const cos = Math.cos(rad);
        const sin = Math.sin(rad);
        const nx = cos * (px - cx) - sin * (py - cy) + cx;
        const ny = sin * (px - cx) + cos * (py - cy) + cy;
        return { x: nx, y: ny };
    };

    const getCapPos = () => {
        const norm = (valCurrent - valMin) / (valMax - valMin || 1);
        const localY = (trackLen / 2) - (norm * trackLen);
        return rotatePoint(x, y + localY, x, y, widgetAngle);
    };

    const draw = (ctx) => {
        const cx = x; const cy = y;
        const ang = widgetAngle;
        const tl = trackLen;

        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);

        // 1. Track
        const p1 = rotatePoint(cx, cy - tl/2, cx, cy, ang);
        const p2 = rotatePoint(cx, cy + tl/2, cx, cy, ang);

        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.lineWidth = 6; ctx.lineCap = "round"; ctx.strokeStyle = "#000"; ctx.stroke();
        ctx.lineWidth = 2; ctx.strokeStyle = "#222"; ctx.stroke();

        // 2. Ticks
        ctx.beginPath(); ctx.lineWidth = 1; ctx.strokeStyle = "#666";
        for (let i = 0; i <= 10; i++) {
            const ly = (tl/2) - (tl * (i/10));
            const len = (i % 5 === 0) ? 10 : 5;
            const t1 = rotatePoint(cx - 15, cy + ly, cx, cy, ang);
            const t2 = rotatePoint(cx - 15 - len, cy + ly, cx, cy, ang);
            ctx.moveTo(t1.x, t1.y); ctx.lineTo(t2.x, t2.y);
            const t3 = rotatePoint(cx + 15, cy + ly, cx, cy, ang);
            const t4 = rotatePoint(cx + 15 + len, cy + ly, cx, cy, ang);
            ctx.moveTo(t3.x, t3.y); ctx.lineTo(t4.x, t4.y);
        }
        ctx.stroke();

        // 3. Cap
        const capPos = getCapPos();
        const r = capRadius;

        ctx.beginPath();
        ctx.arc(capPos.x, capPos.y, r, 0, Math.PI * 2);
        ctx.fillStyle = "#333";
        ctx.fill();
        ctx.lineWidth = isHovered ? 3 : 2;
        ctx.strokeStyle = isHovered ? "#f4902c" : "#888";
        ctx.stroke();

        // 4. Intensity Sweep (Arc)
        const startDeg = 135; 
        const currentDeg = 135 + ((rotCurrent + 130) / 260) * 270;
        const ar = r - 5;
        ctx.strokeStyle = "#f4902c";
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.arc(capPos.x, capPos.y, ar, startDeg * Math.PI / 180, currentDeg * Math.PI / 180);
        ctx.stroke();

        // 5. Pointer
        const ptrAngle = (-90 + rotCurrent) * (Math.PI / 180);
        const ptrLen = (draggingRole === 'cap') ? (r * 10) : (r - 2);
        const pxPos = capPos.x + ptrLen * Math.cos(ptrAngle);
        const pyPos = capPos.y + ptrLen * Math.sin(ptrAngle);

        ctx.beginPath();
        ctx.moveTo(capPos.x, capPos.y);
        ctx.lineTo(pxPos, pyPos);
        ctx.lineWidth = 3; ctx.strokeStyle = "#f4902c"; ctx.stroke();

        // Center dot
        ctx.beginPath(); ctx.arc(capPos.x, capPos.y, 3, 0, Math.PI * 2);
        ctx.fillStyle = "#f4902c"; ctx.fill();

        // Labels
        ctx.font = "10px Arial"; ctx.textAlign = "center"; ctx.fillStyle = "white";
        ctx.fillText(Number(valCurrent).toFixed(1), capPos.x, capPos.y - 35);
        ctx.fillStyle = "#aaaaaa"; ctx.fillText("R:" + Number(rotCurrent).toFixed(0), capPos.x, capPos.y + 35);
    };

    React.useEffect(() => {
        if (canvasRef.current) {
            const ctx = canvasRef.current.getContext('2d');
            draw(ctx);
        }
    }, [valCurrent, rotCurrent, widgetAngle, x, y, isHovered, draggingRole]);

    const handlePointerDown = (e) => {
        const rect = canvasRef.current.getBoundingClientRect();
        const tx = e.clientX - rect.left;
        const ty = e.clientY - rect.top;

        const capPos = getCapPos();
        const dist = Math.sqrt((tx - capPos.x) ** 2 + (ty - capPos.y) ** 2);

        if (dist <= capRadius + 10) {
            setDraggingRole('cap');
            setInteractionState({ startX: tx, startY: ty, startVal: valCurrent, startRot: rotCurrent });
            canvasRef.current.setPointerCapture(e.pointerId);
        } else {
            setDraggingRole('widget_move');
            setInteractionState({ startX: tx, startY: ty, startXPos: x, startYPos: y });
            canvasRef.current.setPointerCapture(e.pointerId);
        }
    };

    const handlePointerMove = (e) => {
        const rect = canvasRef.current.getBoundingClientRect();
        const tx = e.clientX - rect.left;
        const ty = e.clientY - rect.top;

        const capPos = getCapPos();
        const dist = Math.sqrt((tx - capPos.x) ** 2 + (ty - capPos.y) ** 2);
        setIsHovered(dist <= capRadius + 10);

        if (!draggingRole) return;

        if (draggingRole === 'cap') {
            const rad = widgetAngle * (Math.PI / 180);
            const dx = tx - interactionState.startX;
            const dy = ty - interactionState.startY;
            
            const localY = dx * Math.sin(-rad) + dy * Math.cos(-rad);
            const dv = -(localY / trackLen) * 100;
            
            const nextVal = Math.max(valMin, Math.min(valMax, interactionState.startVal + dv));
            
            let nextRot = rotCurrent;
            if (e.shiftKey) {
                nextRot = Math.max(rotMin, Math.min(rotMax, interactionState.startRot + dx));
            }

            if (onChange) onChange({ value: nextVal, rotValue: nextRot, angle: widgetAngle, x, y });
        } else if (draggingRole === 'widget_move') {
            const dx = tx - interactionState.startX;
            const dy = ty - interactionState.startY;
            if (onChange) onChange({ value: valCurrent, rotValue: rotCurrent, angle: widgetAngle, x: interactionState.startXPos + dx, y: interactionState.startYPos + dy });
        }
    };

    const handlePointerUp = (e) => {
        setDraggingRole(null);
        if (canvasRef.current) canvasRef.current.releasePointerCapture(e.pointerId);
    };

    return (
        <canvas
            ref={canvasRef}
            width={800}
            height={800}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            style={{ display: 'block', touchAction: 'none', backgroundColor: '#222' }}
        />
    );
};

window.MDP = MDP;
