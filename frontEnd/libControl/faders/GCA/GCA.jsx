// GCA - Ganged Controlled Array Component
// Author: Anthony Peter Kuzub / Gemini (Collaborator)
// Version: 20260506.1800.1
//
// Description: Multi-channel ganged fader array with macro/micro modes.
// Based on the perfect reference at oaGuiElements/Core/faders/fader_ganged_controlled_array/index.htm

const GCA = ({ config, value, onChange }) => {
    const canvasRef = React.useRef(null);
    const [mode, setMode] = React.useState('macro'); // 'macro' or 'micro'
    const [dragging, setDragging] = React.useState({ master: false, child: -1 });
    const [interactionState, setInteractionState] = React.useState({ startY: 0, startVal: 0 });

    // Schema pillars (canonical) win, with legacy flat keys as a fallback.
    const min = config?.domain?.min !== undefined ? config.domain.min
              : (config?.value_min !== undefined ? config.value_min : 0);
    const max = config?.domain?.max !== undefined ? config.domain.max
              : (config?.value_max !== undefined ? config.value_max : 100);
    const numChannels = config?.num_channels || (config?.channels?.length) || 1;
    const width = config?.layout?.width || 120;
    const height = config?.layout?.height || 400;
    const isRGB = config?.is_rgb === true;

    // Hook MUST be called in the component body, not inside draw() (which runs
    // from a useEffect). Calling it in draw() raises "Invalid hook call".
    const [lang] = window.useMqttLang ? window.useMqttLang() : ['En'];

    // --- State Initialization & Sync ---
    // childVals are the individual fader positions. When no live value has been
    // supplied yet, seed from `config.channels[i].default` so the demo opens at
    // its authored starting point rather than at min on every channel.
    const seedDefaults = () => Array(numChannels).fill(0).map((_, i) => {
        const d = config?.channels?.[i]?.default;
        return (typeof d === 'number') ? d : min;
    });
    let childVals = seedDefaults();
    if (Array.isArray(value)) {
        childVals = value;
    } else if (typeof value === 'object' && value !== null) {
        if (Array.isArray(value.channels)) childVals = value.channels;
        else if (value.value !== undefined) childVals = Array(numChannels).fill(value.value);
    } else if (typeof value === 'number') {
        childVals = Array(numChannels).fill(value);
    }
    
    // Ensure length matches numChannels
    if (childVals.length !== numChannels) {
        const next = Array(numChannels).fill(min);
        childVals.forEach((v, i) => { if (i < numChannels) next[i] = v; });
        childVals = next;
    }

    // --- Stateful master + frozen offsets (faithful to the reference) -------
    // The reference (oaGuiElements/.../fader_ganged_controlled_array/index.htm)
    // keeps `masterVal` and `childOffsets` as instance state. During a master
    // drag, `childVals = clamp(masterVal + childOffsets)` — so the relative
    // offsets between channels stay FIXED. Critically, masterVal does NOT get
    // recomputed from the (possibly clamped) children, so the cap remembers
    // where it was dragged to and a return trip exactly restores the cluster.
    //
    // Offsets are only refreshed when ONE child is moved alone (which is when
    // the user has expressed a new relationship), via `refreshOffsets()`.
    const masterRef = React.useRef(null);
    const offsetsRef = React.useRef(null);
    const lastSeenChildren = React.useRef(null);

    // Detect external value changes (MQTT, parent re-seed, etc.). If our cached
    // children no longer match the prop AND it wasn't a master-drag clamp, we
    // refresh the snapshot from the new values.
    const childrenSignature = (a) => a.join('|');
    const refreshOffsets = (vals) => {
        const m = vals.reduce((s, v) => s + v, 0) / (vals.length || 1);
        masterRef.current = m;
        offsetsRef.current = vals.map(v => v - m);
        lastSeenChildren.current = childrenSignature(vals);
    };
    const ensureSnapshot = () => {
        if (masterRef.current === null || offsetsRef.current === null) {
            refreshOffsets(childVals);
        }
    };
    // If childVals arrived externally (not from our last onChange), re-snapshot.
    const sig = childrenSignature(childVals);
    if (lastSeenChildren.current !== null && lastSeenChildren.current !== sig
        && !(window.__gca_in_master_move)) {
        refreshOffsets(childVals);
    } else if (masterRef.current === null) {
        refreshOffsets(childVals);
    }

    const masterVal = masterRef.current;
    const childOffsets = offsetsRef.current;

    // Apply a new master value: children = clamp(master + offsets). Returns
    // the new childVals array AND updates masterRef in lock-step.
    const applyMaster = (newMaster) => {
        masterRef.current = newMaster;
        const next = (offsetsRef.current || []).map(o => Math.max(min, Math.min(max, newMaster + o)));
        lastSeenChildren.current = childrenSignature(next);
        return next;
    };

    // --- Coordinate Mapping ---
    const getY = (val) => {
        const range = max - min;
        const norm = (val - min) / (range || 1);
        const drawH = height - 40; // 20px margin top/bottom
        return 20 + drawH * (1.0 - norm);
    };

    const getVal = (y) => {
        const drawH = height - 40;
        const norm = (drawH - (y - 20)) / drawH;
        return min + (norm * (max - min));
    };

    // --- Color Logic (Refined from perfect source) ---
    const getColor = (norm, index) => {
        if (isRGB) {
            const intensity = Math.max(50, Math.floor(norm * 255));
            if (index === 0) return `rgb(${intensity}, 0, 0)`; // Red
            if (index === 1) return `rgb(0, ${intensity}, 0)`; // Green
            if (index === 2) return `rgb(0, 0, ${intensity})`; // Blue
            if (index === -1) { // Mix color for master
                const r = Math.floor((childVals[0] / max) * 255);
                const g = Math.floor((childVals[1] / max) * 255);
                const b = Math.floor((childVals[2] / max) * 255);
                return `rgb(${r},${g},${b})`;
            }
        }

        // Default Heat Gradient: Green -> Yellow -> Red
        let r, g, b;
        if (norm < 0.5) {
            r = Math.floor(255 * (norm * 2));
            g = 255;
            b = 0;
        } else {
            r = 255;
            g = Math.floor(255 * (1.0 - (norm - 0.5) * 2));
            b = 0;
        }
        return `rgb(${r},${g},${b})`;
    };

    // --- Canvas Rendering ---
    const draw = (ctx) => {
        ctx.fillStyle = "#222";
        ctx.fillRect(0, 0, width, height);

        const stripW = numChannels > 0 ? width / numChannels : width;
        const accentColor = config?.active_color || "#f4902c";

        // 1. Draw Channels (Tracks & Dividers)
        for (let i = 0; i < numChannels; i++) {
            const cx = (i * stripW) + (stripW / 2);
            
            // Channel Track
            ctx.strokeStyle = "#444";
            ctx.lineWidth = 4;
            ctx.lineCap = "round";
            ctx.beginPath();
            ctx.moveTo(cx, 20);
            ctx.lineTo(cx, height - 20);
            ctx.stroke();

            // Channel Divider (Dashed)
            if (i > 0) {
                ctx.strokeStyle = "#333";
                ctx.lineWidth = 1;
                ctx.setLineDash([2, 4]);
                ctx.beginPath();
                ctx.moveTo(i * stripW, 20);
                ctx.lineTo(i * stripW, height - 20);
                ctx.stroke();
                ctx.setLineDash([]);
            }

            // Channel Value Marker
            const val = childVals[i];
            const y = getY(val);
            const norm = (val - min) / (max - min || 1);
            ctx.strokeStyle = getColor(norm, i);
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.moveTo(cx - stripW * 0.3, y);
            ctx.lineTo(cx + stripW * 0.3, y);
            ctx.stroke();
        }

        // 2. Draw Cap Component
        const capH = 60;
        const capY = getY(masterVal);
        const capW = width - 10;
        const capX = 5;

        // Master Fill Highlights (on tracks from bottom up to cap)
        ctx.strokeStyle = accentColor;
        ctx.lineWidth = 2;
        for (let i = 0; i < numChannels; i++) {
            const tcx = (i * stripW) + (stripW / 2);
            ctx.beginPath();
            ctx.moveTo(tcx, height - 20);
            ctx.lineTo(tcx, capY);
            ctx.stroke();
        }

        // Cap Outer Body
        ctx.fillStyle = "#333";
        ctx.strokeStyle = accentColor;
        ctx.lineWidth = 2;
        
        const r = 8; // Corner radius
        ctx.beginPath();
        ctx.moveTo(capX + r, capY - capH / 2);
        ctx.arcTo(capX + capW, capY - capH / 2, capX + capW, capY + capH / 2, r);
        ctx.arcTo(capX + capW, capY + capH / 2, capX, capY + capH / 2, r);
        ctx.arcTo(capX, capY + capH / 2, capX, capY - capH / 2, r);
        ctx.arcTo(capX, capY - capH / 2, capX + capW, capY - capH / 2, r);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        // Inner "Screen" area
        const margin = 4;
        const sx = capX + margin;
        const sy = capY - capH / 2 + margin;
        const sw = capW - margin * 2;
        const sh = capH - margin * 2;
        ctx.fillStyle = "black";
        ctx.fillRect(sx, sy, sw, sh);

        // Cap Visualization Logic
        if (mode === "macro" || numChannels <= 1) {
            const norm = (masterVal - min) / (max - min || 1);
            const barW = sw * 0.9;
            const barH = 10;
            const bx = sx + (sw - barW) / 2;
            const by = sy + (sh - barH) / 2;
            ctx.fillStyle = getColor(norm, -1); // Mix color or gradient
            ctx.fillRect(bx, by, barW, barH);
            
            ctx.fillStyle = "white";
            ctx.font = "12px Arial";
            ctx.textAlign = "center";
            ctx.fillText(masterVal.toFixed(1), sx + sw / 2, sy + sh / 2 + 20);
            
            ctx.fillStyle = "#888";
            ctx.font = "10px Arial";
            ctx.fillText(isRGB ? "COLOR" : (config.sub_label || "AVG"), sx + sw / 2, sy + sh / 2 - 10);
        } else {
            const microW = sw / numChannels;
            for (let i = 0; i < numChannels; i++) {
                const val = childVals[i];
                const norm = (val - min) / (max - min || 1);
                const mx = sx + (i * microW);
                const fillH = norm * sh;
                
                ctx.fillStyle = "#222";
                ctx.fillRect(mx + 1, sy, microW - 2, sh);
                ctx.fillStyle = getColor(norm, i);
                ctx.fillRect(mx + 1, sy + sh - fillH, microW - 2, fillH);
                
                // Channel Labels/Numbers (lang resolved in component body above)
                const chanCfg = config.channels?.[i] || {};
                const chanLabel = chanCfg.label?.[lang] || chanCfg.label?.En || (i + 1);

                ctx.fillStyle = "white";
                ctx.font = "7px Arial";
                ctx.textAlign = "center";
                ctx.fillText(chanLabel, mx + microW / 2, sy + sh - 2);
            }
        }
    };

    React.useEffect(() => {
        if (canvasRef.current) {
            const ctx = canvasRef.current.getContext('2d');
            draw(ctx);
        }
    }, [childVals, masterVal, mode]);

    // React onWheel is PASSIVE — preventDefault is a no-op. To stop the page
    // from scrolling while the wheel fine-tunes the master, attach a native
    // non-passive listener. (Same trick used by Knob/FaderDial.)
    React.useEffect(() => {
        const c = canvasRef.current;
        if (!c) return undefined;
        const onWheelNative = (e) => {
            e.preventDefault();
            ensureSnapshot();
            const delta = Math.sign(e.deltaY) * -1;
            const step = (max - min) * 0.05;
            const nextMaster = Math.max(min, Math.min(max, masterRef.current + (delta * step)));
            window.__gca_in_master_move = true;
            const nextVals = applyMaster(nextMaster);
            onChange(nextVals);
            window.__gca_in_master_move = false;
        };
        c.addEventListener('wheel', onWheelNative, { passive: false });
        return () => c.removeEventListener('wheel', onWheelNative);
    }, [masterVal, min, max, childVals, onChange]);

    // --- Interaction Handlers ---
    const handlePointerDown = (e) => {
        const rect = canvasRef.current.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const capY = getY(masterVal);
        const capTop = capY - 30;
        const capBottom = capY + 30;

        if (y >= capTop && y <= capBottom) {
            // Hit the cap
            if (mode === "micro" && numChannels > 1) {
                const margin = 4;
                const capW = width - 10;
                const sx = 5 + margin;
                const sw = capW - margin * 2;
                if (x >= sx && x <= sx + sw) {
                    const relX = x - sx;
                    const colW = sw / numChannels;
                    const idx = Math.floor(relX / colW);
                    if (idx >= 0 && idx < numChannels) {
                        setDragging({ master: false, child: idx });
                        setInteractionState({ startY: e.clientY, startVal: childVals[idx] });
                        canvasRef.current.setPointerCapture(e.pointerId);
                        return;
                    }
                }
            }
            setDragging({ master: true, child: -1 });
            setInteractionState({ startY: e.clientY, startVal: masterVal });
            canvasRef.current.setPointerCapture(e.pointerId);
        } else {
            // Clicked on track -> Jump master (children follow by offset)
            ensureSnapshot();
            const val = Math.max(min, Math.min(max, getVal(y)));
            window.__gca_in_master_move = true;
            const nextVals = applyMaster(val);
            onChange(nextVals);
            window.__gca_in_master_move = false;
            setDragging({ master: true, child: -1 });
            setInteractionState({ startY: e.clientY, startVal: val });
            canvasRef.current.setPointerCapture(e.pointerId);
        }
    };

    const handlePointerMove = (e) => {
        if (dragging.master) {
            const rect = canvasRef.current.getBoundingClientRect();
            const y = e.clientY - rect.top;
            const currentVal = Math.max(min, Math.min(max, getVal(y)));
            // Reference behaviour: master is independent state, children =
            // clamp(master + offsets). Offsets stay frozen during the drag —
            // a channel that clamps at max/min un-clamps perfectly when the
            // master returns to its earlier position.
            window.__gca_in_master_move = true;
            const nextVals = applyMaster(currentVal);
            onChange(nextVals);
            window.__gca_in_master_move = false;
        } else if (dragging.child >= 0) {
            const dy = interactionState.startY - e.clientY;
            const pixelRange = height - 40;
            const valRange = max - min;
            const deltaVal = (dy / pixelRange) * valRange;
            const newVal = Math.max(min, Math.min(max, interactionState.startVal + deltaVal));
            const nextVals = [...childVals];
            nextVals[dragging.child] = newVal;
            // Single child moved → user has re-expressed the relationship, so
            // refresh master = avg(children) AND recompute offsets. (Same as
            // reference's updateMasterFromChildren + recalculateOffsets.)
            refreshOffsets(nextVals);
            onChange(nextVals);
        }
    };

    const handlePointerUp = (e) => {
        setDragging({ master: false, child: -1 });
        if (canvasRef.current) canvasRef.current.releasePointerCapture(e.pointerId);
    };

    // (Native non-passive wheel listener is registered in the useEffect above;
    // React's onWheel is passive so preventDefault() would no-op here.)

    const handleDoubleClick = () => {
        setMode(m => m === 'macro' ? 'micro' : 'macro');
    };

    return (
        <div className="gca-wrapper" style={{ 
            backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, '#3c3f41') : '#3c3f41'), 
            border: '1px solid #555', 
            borderTop: `3px solid ${config?.active_color || '#f4902c'}`, 
            padding: '10px', 
            borderRadius: '4px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            boxShadow: '0 4px 15px rgba(0,0,0,0.3)'
        }}>
            <div className="widget-label" style={{ marginBottom: '10px', fontWeight: 'bold', color: '#dcdcdc', fontSize: '11px' }}>
                {String(
                    (config?.label?.active?.text?.En)
                    || (config?.label_active?.En)
                    || (config?.label?.En)
                    || (typeof config?.label === 'string' ? config.label : null)
                    || "GCA"
                ).toUpperCase()}
            </div>
            <canvas
                ref={canvasRef}
                width={width}
                height={height}
                onPointerDown={handlePointerDown}
                onPointerMove={handlePointerMove}
                onPointerUp={handlePointerUp}
                onDoubleClick={handleDoubleClick}
                style={{ cursor: 'pointer', backgroundColor: '#222', borderRadius: '4px', touchAction: 'none' }}
            />
        </div>
    );
};

window.GCA = GCA;