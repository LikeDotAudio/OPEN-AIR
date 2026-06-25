// CMDP - Circular Motion Displacement Potentiometer Component
// Author: Gemini (Collaborator)
// Version: 20260506.1700.1
//
// Description: Polar-coordinate panner/fader.

const CMDP = ({ config, value, rotValue, onChange }}) => {
    const canvasRef = React.useRef(null);
    const [dragging, setDragging] = React.useState(false);
    const [interactionState, setInteractionState] = React.useState({ startX: 0, startY: 0, startVal: 0, startRot: 0, startAngle: 0 }});

    const NEAR_RADIUS = 120;
    const FAR_RADIUS = 380;
    const trackLen = FAR_RADIUS - NEAR_RADIUS;

    // --- Robust Value Extraction ---
    const getVal = (v, fallback) => (typeof v === 'number' ? v : (typeof v === 'string' ? parseFloat(v) : fallback));
    
    let valCurrent = 50;
    let rotCurrent = 0;
    let angle = config?.angle !== undefined ? config.angle : 0;

    if (value && typeof value === 'object' && !Array.isArray(value)) {
        valCurrent = getVal(value.value, valCurrent);
        rotCurrent = getVal(value.rotValue, rotCurrent);
        if (value.angle !== undefined) angle = getVal(value.angle, angle);
    }} else {
        valCurrent = getVal(value, valCurrent);
        rotCurrent = getVal(rotValue, rotCurrent);
    }}

    const colorHighlight = config?.color || "#f4902c";
    const label = config?.label || "CMDP";

    const draw = (ctx, w, h) => {
        const cx = w / 2;
        const cy = h / 2;

        ctx.fillStyle = "#222";
        ctx.fillRect(0, 0, w, h);

        // Guidelines
        ctx.strokeStyle = "#f4902c";
        ctx.setLineDash([5, 5]);
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(cx, cy, NEAR_RADIUS, 0, Math.PI * 2); ctx.stroke();
        ctx.beginPath(); ctx.arc(cx, cy, FAR_RADIUS, 0, Math.PI * 2); ctx.stroke();
        ctx.setLineDash([]);

        // Fader Track
        const rad = angle * Math.PI / 180;
        const x1 = cx + NEAR_RADIUS * Math.cos(rad);
        const y1 = cy + NEAR_RADIUS * Math.sin(rad);
        const x2 = cx + FAR_RADIUS * Math.cos(rad);
        const y2 = cy + FAR_RADIUS * Math.sin(rad);

        ctx.save();
        const dist = NEAR_RADIUS + (trackLen / 2);
        const fx = cx + dist * Math.cos(rad);
        const fy = cy + dist * Math.sin(rad);
        
        ctx.translate(fx, fy);
        ctx.rotate((angle + 90) * Math.PI / 180);
        
        ctx.lineCap = "round";
        ctx.lineWidth = 6; ctx.strokeStyle = "#000"; ctx.beginPath(); ctx.moveTo(0, -trackLen/2); ctx.lineTo(0, trackLen/2); ctx.stroke();
        ctx.lineWidth = 2; ctx.strokeStyle = "#222"; ctx.beginPath(); ctx.moveTo(0, -trackLen/2); ctx.lineTo(0, trackLen/2); ctx.stroke();
        
        const norm = valCurrent / 100;
        const capY = (-trackLen / 2) + (norm * trackLen);
        
        ctx.translate(0, capY);
        ctx.rotate(-((angle + 90) * Math.PI / 180));
        
        const r = 22;
        ctx.fillStyle = "#333";
        ctx.strokeStyle = dragging ? "#fff" : colorHighlight;
        ctx.lineWidth = dragging ? 3 : 2;
        ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
        
        const startDeg = 135; 
        const currentDeg = 135 + (rotCurrent / 100) * 270;
        const ar = r - 5;
        ctx.strokeStyle = colorHighlight;
        ctx.lineWidth = 4;
        ctx.beginPath(); 
        ctx.arc(0, 0, ar, startDeg * Math.PI / 180, currentDeg * Math.PI / 180); 
        ctx.stroke();
        
        const indRad = currentDeg * (Math.PI / 180);
        ctx.lineWidth = 3;
        ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo((r-2)*Math.cos(indRad), (r-2)*Math.sin(indRad)); ctx.stroke();
        
        ctx.fillStyle = "#fff"; ctx.font = "10px Arial"; ctx.textAlign = "center";
        ctx.fillText(valCurrent.toFixed(1), 0, -30);
        ctx.restore();

        // Label at perimeter
        const labDist = FAR_RADIUS + 40;
        const lx = cx + labDist * Math.cos(rad);
        const ly = cy + labDist * Math.sin(rad);
        ctx.save();
        ctx.translate(lx, ly);
        ctx.rotate((angle + 90) * Math.PI / 180);
        ctx.fillStyle = colorHighlight; ctx.font = "bold 12px Arial"; ctx.textAlign = "center";
        ctx.fillText(label, 0, 0);
        ctx.restore();
    }};

    React.useEffect(() => {
        if (canvasRef.current) {
            const ctx = canvasRef.current.getContext('2d');
            const w = canvasRef.current.width;
            const h = canvasRef.current.height;
            draw(ctx, w, h);
        }}
    }}, [valCurrent, rotCurrent, angle, dragging]);

    const handlePointerDown = (e) => {
        const rect = canvasRef.current.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;
        const cx = rect.width / 2;
        const cy = rect.height / 2;

        const rad = angle * Math.PI / 180;
        const dist = NEAR_RADIUS + (trackLen / 2);
        const fx = cx + dist * Math.cos(rad);
        const fy = cy + dist * Math.sin(rad);
        
        const norm = valCurrent / 100;
        const capYRel = (-trackLen / 2) + (norm * trackLen);
        
        // Final cap position in canvas space
        const angRad = (angle + 90) * Math.PI / 180;
        const capX = fx + capYRel * Math.sin(-angRad);
        const capY = fy + capYRel * Math.cos(angRad);

        const hitDist = Math.sqrt((mx - capX) ** 2 + (my - capY) ** 2);
        if (hitDist < 30) {
            setDragging(true);
            setInteractionState({ startX: mx, startY: my, startVal: valCurrent, startRot: rotCurrent, startAngle: angle }});
            canvasRef.current.setPointerCapture(e.pointerId);
        }}
    }};

    const handlePointerMove = (e) => {
        if (!dragging) return;
        const rect = canvasRef.current.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;
        const cx = rect.width / 2;
        const cy = rect.height / 2;

        if (e.buttons === 1) { // Left drag: Depth
            const rad = angle * Math.PI / 180;
            const tx = Math.cos(rad);
            const ty = Math.sin(rad);
            const dx = mx - interactionState.startX;
            const dy = my - interactionState.startY;
            const proj = dx * tx + dy * ty; 
            const change = -(proj / trackLen) * 100; 
            const nextVal = Math.max(0, Math.min(100, interactionState.startVal + change));
            if (onChange) onChange({ value: nextVal, rotValue: rotCurrent, angle }});
        }} else if (e.buttons === 2) { // Right drag: Intensity
            const dx = mx - interactionState.startX;
            const nextRot = Math.max(0, Math.min(100, interactionState.startRot + dx * 0.5));
            if (onChange) onChange({ value: valCurrent, rotValue: nextRot, angle }});
        }} else if (e.altKey) { // Alt + Drag: Azimuth
            const dx = mx - cx;
            const dy = my - cy;
            const nextAngle = Math.atan2(dy, dx) * 180 / Math.PI;
            if (onChange) onChange({ value: valCurrent, rotValue: rotCurrent, angle: nextAngle }});
        }}
    }};

    const handlePointerUp = (e) => {
        setDragging(false);
        if (canvasRef.current) canvasRef.current.releasePointerCapture(e.pointerId);
    }};

    return (
        <canvas
            ref={canvasRef}
            width={1000}
            height={1000}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onContextMenu={e => e.preventDefault()}
            style={{ display: 'block', cursor: 'default', touchAction: 'none' }}}
        />
    );
};

window.CMDP = CMDP;
