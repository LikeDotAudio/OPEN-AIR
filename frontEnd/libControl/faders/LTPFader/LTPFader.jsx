// LTPFader - Linear Travelling Potentiometer Component
// Author: Gemini (Collaborator)
// Version: 20260506.1600.1
//
// Description: Dual-axis controller (linear travel + rotation).

const LTPFader = ({ config, value, rotValue, onChange }) => {
    const canvasRef = React.useRef(null);
    const [dragging, setDragging] = React.useState(false);
    const [isMod, setIsMod] = React.useState(false);
    const [interactionState, setInteractionState] = React.useState({ startX: 0, startY: 0, startLin: 0, startRot: 0 });

    const min = config?.min || 0;
    const max = config?.max || 100;
    const rotMin = -100;
    const rotMax = 100;
    const width = config?.width || 100;
    const height = config?.height || 300;
    const radius = 18;
    const freestyle = config?.freestyle || false;

    // --- Robust Value Extraction ---
    // If 'value' is an object (composite state from MQTT), extract parts.
    // Otherwise fallback to primitive 'value' and 'rotValue' props.
    const getVal = (v, fallback) => (typeof v === 'number' ? v : (typeof v === 'string' ? parseFloat(v) : fallback));
    
    let linearVal = (min + max) / 2;
    let currentRotVal = 0;

    if (value && typeof value === 'object' && !Array.isArray(value)) {
        linearVal = getVal(value.value, linearVal);
        currentRotVal = getVal(value.rotValue, currentRotVal);
    } else {
        linearVal = getVal(value, linearVal);
        currentRotVal = getVal(rotValue, currentRotVal);
    }

    const getHandleY = (val) => {
        const range = max - min;
        const norm = (val - min) / range;
        const drawH = height - 40;
        return 20 + drawH * (1.0 - norm);
    };

    const getValFromY = (y) => {
        const drawH = height - 40;
        const norm = (drawH - (y - 20)) / drawH;
        return min + (norm * (max - min));
    };

    const draw = (ctx) => {
        const cx = width / 2;
        const isNarrow = width < 50;
        const isAdjustingPot = dragging && (isMod || freestyle);

        ctx.fillStyle = "#222";
        ctx.fillRect(0, 0, width, height);

        ctx.strokeStyle = "#444";
        ctx.lineWidth = 4;
        ctx.lineCap = "round";
        ctx.beginPath();
        ctx.moveTo(cx, 20);
        ctx.lineTo(cx, height - 20);
        ctx.stroke();

        const handleY = getHandleY(linearVal);
        ctx.strokeStyle = freestyle ? "#FF5555" : "#f4902c";
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.moveTo(cx, height - 20);
        ctx.lineTo(cx, handleY);
        ctx.stroke();

        const range = max - min;
        const steps = isNarrow ? 5 : 10;
        ctx.strokeStyle = "#666";
        ctx.lineWidth = 1;
        ctx.font = isNarrow ? "7px Arial" : "10px Arial";
        ctx.fillStyle = "#888";
        ctx.textAlign = "left";

        for (let i = 0; i <= steps; i++) {
            const norm = i / steps;
            const y = 20 + (height - 40) * (1.0 - norm);
            const val = min + (norm * range);
            ctx.beginPath();
            const tw = isNarrow ? 5 : 10;
            ctx.moveTo(cx - tw, y);
            ctx.lineTo(cx + tw, y);
            ctx.stroke();
            if (i % 2 === 0 && !isNarrow) {
                ctx.fillText(val.toFixed(0), cx + 15, y + 3);
            }
        }

        ctx.fillStyle = "#dcdcdc";
        ctx.beginPath();
        ctx.arc(cx, handleY, radius, 0, Math.PI * 2);
        ctx.fill();

        const angle = (currentRotVal / 100) * 135;
        const rad = (angle - 90) * Math.PI / 180;
        const drawLen = isAdjustingPot ? radius * 10 : radius;
        const px = cx + drawLen * Math.cos(rad);
        const py = handleY + drawLen * Math.sin(rad);

        ctx.strokeStyle = "#f4902c";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(cx, handleY);
        ctx.lineTo(px, py);
        ctx.stroke();

        ctx.fillStyle = "#f4902c";
        ctx.beginPath();
        ctx.arc(cx, handleY, 3, 0, Math.PI * 2);
        ctx.fill();

        if (!isNarrow) {
            ctx.fillStyle = "#fff";
            ctx.textAlign = "right";
            ctx.fillText(`L: ${linearVal.toFixed(1)}`, cx - 25, handleY + 4);
            ctx.textAlign = "left";
            ctx.fillText(`R: ${currentRotVal.toFixed(0)}`, cx + 25, handleY + 4);
        }
    };

    React.useEffect(() => {
        if (canvasRef.current) {
            const ctx = canvasRef.current.getContext('2d');
            draw(ctx);
        }
    }, [linearVal, currentRotVal, dragging, isMod]);

    const handlePointerDown = (e) => {
        const rect = canvasRef.current.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const handleY = getHandleY(linearVal);
        const cx = width / 2;
        const dist = Math.sqrt((x - cx) ** 2 + (y - handleY) ** 2);

        if (dist <= radius * 1.5) {
            setDragging(true);
            setIsMod(e.altKey);
            setInteractionState({ startX: x, startY: y, startLin: linearVal, startRot: currentRotVal });
            canvasRef.current.setPointerCapture(e.pointerId);
        }
    };

    const handlePointerMove = (e) => {
        if (!dragging) return;
        const rect = canvasRef.current.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const activeMod = e.altKey;
        if (!freestyle && activeMod !== isMod) {
            setInteractionState(prev => ({ ...prev, startX: x, startY: y, startLin: linearVal, startRot: currentRotVal }));
            setIsMod(activeMod);
        }

        let nextLin = linearVal;
        let nextRot = currentRotVal;

        if (freestyle || activeMod) {
            const dx = x - interactionState.startX;
            const sensitivity = 0.5;
            let change = dx * sensitivity;
            if (freestyle) change /= 2;
            nextRot = Math.max(rotMin, Math.min(rotMax, interactionState.startRot + change));
        }

        if (freestyle || !activeMod) {
            const dy = y - interactionState.startY;
            const pixelRange = height - 40;
            const valRange = max - min;
            let change = -(dy / pixelRange) * valRange;
            if (freestyle) change /= 2;
            nextLin = Math.max(min, Math.min(max, interactionState.startLin + change));
        }

        if (onChange) {
            onChange({ value: nextLin, rotValue: nextRot });
        }
    };

    const handlePointerUp = (e) => {
        setDragging(false);
        if (canvasRef.current) canvasRef.current.releasePointerCapture(e.pointerId);
    };

    return (
        <div className="ltp-wrapper" style={{ 
            backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, '#3c3f41') : '#3c3f41'), 
            border: '1px solid #555', 
            padding: '10px', 
            borderRadius: '4px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center'
        }}>
            <div className="widget-label" style={{ 
                marginBottom: '10px', 
                fontWeight: 'bold', 
                color: '#dcdcdc',
                fontSize: width < 40 ? '8px' : '12px'
            }}>
                {config?.label || "LTP"}
            </div>
            <canvas
                ref={canvasRef}
                width={width}
                height={height}
                onPointerDown={handlePointerDown}
                onPointerMove={handlePointerMove}
                onPointerUp={handlePointerUp}
                style={{ 
                    cursor: freestyle ? 'move' : (isMod ? 'ew-resize' : 'ns-resize'), 
                    backgroundColor: '#222', 
                    borderRadius: '4px', 
                    touchAction: 'none' 
                }}
            />
        </div>
    );
};

window.LTPFader = LTPFader;
