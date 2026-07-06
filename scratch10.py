import re

with open('FrontEnd/libControl/faders/LTPFader/LTPFader.jsx', 'r') as f:
    code = f.read()

# 1. Inside draw(), handle isWbsElma
code = code.replace("const handlePos = getHandlePos(linearVal);", "const handlePos = getHandlePos(linearVal);\n        const isWbsElma = (kc?.knob_style === 'wbs-elma');")

old_cap_draw = """        // -- Travelling cap ---------------------------------------------------
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

        // Rotation indicator: mapped from rotMin..rotMax to +/-135deg. When adjusting
        // the pot the line extends 10x so the sweep is legible off the cap.
        const rotRange = (rotMax - rotMin) || 200;
        const normalizedRot = ((currentRotVal - rotMin) / rotRange) * 2 - 1;
        const angle = normalizedRot * 135;
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
        ctx.fill();"""

new_cap_draw = """        // -- Travelling cap ---------------------------------------------------
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

            // Rotation indicator
            const rotRange = (rotMax - rotMin) || 200;
            const normalizedRot = ((currentRotVal - rotMin) / rotRange) * 2 - 1;
            const angle = normalizedRot * 135;
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
        }"""
code = code.replace(old_cap_draw, new_cap_draw)

# 2. Add React render for WBSElma
old_return = """            <div style={{ position: 'relative', width, height }}>
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
            </div>"""

new_return = """            <div style={{ position: 'relative', width, height }}>
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
                {(kc?.knob_style === 'wbs-elma') && window.KnobCapWBSElma && (
                    <div style={{
                        position: 'absolute',
                        left: (isHorizontal ? getHandlePos(linearVal) : width / 2) - capRadius,
                        top: (isHorizontal ? height / 2 : getHandlePos(linearVal)) - capRadius,
                        width: capRadius * 2,
                        height: capRadius * 2,
                        pointerEvents: 'none'
                    }}>
                        <window.KnobCapWBSElma 
                            val={currentRotVal} 
                            min={rotMin} 
                            max={rotMax} 
                            width={capRadius * 2}
                            height={capRadius * 2}
                            cosmetics={{
                                styling: {
                                    fill_color: "#546E7A",
                                    cap_color: kc?.cap_color || capAccent,
                                    outline_color: "#000",
                                    outline_thickness: 1
                                },
                                flutes: 18,
                                cap: { show: true, color: kc?.cap_color || capAccent },
                                wing: { show: false },
                                pointer_tip: { show: true, color: "#546E7A", length: 0.2 },
                                line: { color: "#ffffff" }
                            }}
                        />
                    </div>
                )}
            </div>"""

code = code.replace(old_return, new_return)

with open('FrontEnd/libControl/faders/LTPFader/LTPFader.jsx', 'w') as f:
    f.write(code)

