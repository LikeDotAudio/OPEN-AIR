import re

with open("FrontEnd/libControl/faders/LTPFader/LTPFader.jsx", "r") as f:
    code = f.read()

# 1. Add isHorizontal
code = code.replace(
    "    const freestyle = !!(config?.interaction?.freestyle || fc?.freestyle || config?.freestyle);",
    "    const freestyle = !!(config?.interaction?.freestyle || fc?.freestyle || config?.freestyle);\n    const isHorizontal = width > height;"
)

# 2. Update getHandleY to getHandlePos
code = code.replace(
    """    // -- Coordinate mapping ---------------------------------------------------
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
    };""",
    """    // -- Coordinate mapping ---------------------------------------------------
    const getHandlePos = (val) => {
        const range = (max - min) || 1;
        const norm = (val - min) / range;
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
            return min + (norm * (max - min));
        } else {
            const drawH = height - 40;
            const norm = (drawH - (y - 20)) / drawH;
            return min + (norm * (max - min));
        }
    };"""
)

# 3. Update draw method
code = code.replace(
    """    // -- Rail + travelling cap render (canvas) --------------------------------
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
    };""",
    """    // -- Rail + travelling cap render (canvas) --------------------------------
    const draw = (ctx) => {
        const cx = width / 2;
        const cy = height / 2;
        const isNarrow = isHorizontal ? height < 50 : width < 50;

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

        // Rotation indicator: rotVal (-100..100) → +/-135deg. When adjusting
        // the pot the line extends 10x so the sweep is legible off the cap.
        const angle = (currentRotVal / 100) * 135;
        const rad = (angle - 90) * Math.PI / 180;
        const drawLen = isAdjustingPot ? capRadius * 10 : capRadius;
        const px = hx + drawLen * Math.cos(rad);
        const py = hy + drawLen * Math.sin(rad);
        ctx.strokeStyle = capAccent;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(hx, hy);
        ctx.lineTo(px, py);
        ctx.stroke();

        // Center dot
        ctx.fillStyle = capAccent;
        ctx.beginPath();
        ctx.arc(hx, hy, 3, 0, Math.PI * 2);
        ctx.fill();

        // -- Numerics ---------------------------------------------------------
        if (!isNarrow) {
            if (showVal) {
                ctx.fillStyle = '#fff';
                ctx.font = '10px Arial';
                const lTxt = `L: ${linearVal.toFixed(1)}${showUnits && unitText ? ' ' + unitText : ''}`;
                if (isHorizontal) {
                    ctx.textAlign = 'right';
                    ctx.fillText(lTxt, hx - 25, hy - 25);
                    ctx.textAlign = 'left';
                    ctx.fillText(`R: ${currentRotVal.toFixed(0)}`, hx + 25, hy - 25);
                } else {
                    ctx.textAlign = 'right';
                    ctx.fillText(lTxt, cx - 25, hy + 4);
                    ctx.textAlign = 'left';
                    ctx.fillText(`R: ${currentRotVal.toFixed(0)}`, cx + 25, hy + 4);
                }
            }
            if (freestyle) {
                ctx.textAlign = 'center';
                ctx.fillStyle = '#FF5555';
                ctx.font = 'bold 10px Arial';
                ctx.fillText('FREESTYLE', cx, isHorizontal ? height - 5 : height - 5);
            }
        } else if (showVal) {
            ctx.fillStyle = '#000';
            ctx.textAlign = 'center';
            ctx.font = '7px Arial';
            ctx.fillText(`${linearVal.toFixed(0)}`, hx, hy + 3);
        }
    };"""
)

# 4. Update Interaction
code = code.replace(
    """    const isOverHandle = (x, y) => {
        const hy = getHandleY(linearVal);
        const cx = width / 2;
        const hit = capRadius * 1.5;   // generous hit area (touch-friendly)
        return Math.hypot(x - cx, y - hy) <= hit;
    };""",
    """    const isOverHandle = (x, y) => {
        const hp = getHandlePos(linearVal);
        const hx = isHorizontal ? hp : width / 2;
        const hy = isHorizontal ? height / 2 : hp;
        const hit = capRadius * 1.5;   // generous hit area (touch-friendly)
        return Math.hypot(x - hx, y - hy) <= hit;
    };"""
)

code = code.replace(
    """            const v = Math.max(min, Math.min(max, getValFromY(y)));""",
    """            const v = Math.max(min, Math.min(max, getValFromPos(x, y)));"""
)

code = code.replace(
    """        if (rotActive) {
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
        }""",
    """        if (rotActive) {
            const dRot = isHorizontal ? (d.startY - y) : (x - d.startX);
            let change = dRot * 0.5;
            if (freestyle) change /= 2;
            nextRot = Math.max(rotMin, Math.min(rotMax, d.startRot + change));
        }
        if (linActive) {
            let change = 0;
            if (isHorizontal) {
                change = ((x - d.startX) / (width - 40)) * (max - min);
            } else {
                change = -((y - d.startY) / (height - 40)) * (max - min);
            }
            if (freestyle) change /= 2;
            nextLin = Math.max(min, Math.min(max, d.startLin + change));
        }"""
)

with open("FrontEnd/libControl/faders/LTPFader/LTPFader.jsx", "w") as f:
    f.write(code)

print("Modifications written successfully!")
