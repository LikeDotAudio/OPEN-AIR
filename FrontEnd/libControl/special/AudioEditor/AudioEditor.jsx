const AudioEditor = ({ label = "Wave Audio Editor" }) => {
    const KIT = window.OA_DRUM_KIT || [];
    const getCtx = () => (window.oaAudioCtx ? window.oaAudioCtx()
        : new (window.AudioContext || window.webkitAudioContext)());

    const canvasRef = React.useRef(null);
    const waveWrapRef = React.useRef(null);
    const previewSrcRef = React.useRef(null);
    const rafRef = React.useRef(null);

    const [audioBuffer, setAudioBuffer] = React.useState(null);
    const [fileName, setFileName] = React.useState('');
    const [isPlaying, setIsPlaying] = React.useState(false);

    // All positions are fractions (0..1) of the FULL buffer.
    const [selection, setSelection] = React.useState({ start: 0.2, end: 0.8 });
    const [view, setView] = React.useState({ start: 0, end: 1 });   // zoom window
    const [cursor, setCursor] = React.useState(0.5);                // I/O anchor
    const [playhead, setPlayhead] = React.useState(null);           // 0..1 or null

    // Assignment options
    const [selectedPad, setSelectedPad] = React.useState(0);
    const [autoLoop, setAutoLoop] = React.useState(false);
    const [fade, setFade] = React.useState(false);
    const [pitchSemi, setPitchSemi] = React.useState(0);            // -12..+12
    const [samples, setSamples] = React.useState([]);               // captured list
    const [dragOver, setDragOver] = React.useState(false);          // drag-and-drop
    const [loadError, setLoadError] = React.useState('');
    const [playingWhich, setPlayingWhich] = React.useState(null);   // 'in' | 'cursor' | 'seven'
    const mqttPublish = window.useMqttPublish ? window.useMqttPublish() : null;
    const [browsing, setBrowsing] = React.useState(false);          // Sound Browse open
    const [loadedFolder, setLoadedFolder] = React.useState('');     // source folder of loaded file
    const fileInputRef = React.useRef(null);

    const padName = (i) => (KIT[i] && KIT[i].name) || `Pad ${i + 1}`;
    const selectedHasSample = !!(window.OA_DRUM_SAMPLES && window.OA_DRUM_SAMPLES[selectedPad]);

    // ---- File load -----------------------------------------------------------
    const handleFile = async (file, folder) => {
        if (!file) return;
        setLoadError('');
        setLoadedFolder(folder || '');
        try {
            const ctx = getCtx();
            const arrayBuffer = await file.arrayBuffer();
            // oaDecodeAudio handles wav/mp3/aac/m4a/ogg/flac via the browser, and
            // AIFF/AIFC via a hand-written parser (Chromium can't decode AIFF).
            const decoded = await window.oaDecodeAudio(ctx, arrayBuffer);
            setFileName(file.name);
            setAudioBuffer(decoded);
            setView({ start: 0, end: 1 });
            setSelection({ start: 0, end: 1 });   // whole file — no trimmed in/out
            setCursor(0);
        } catch (err) {
            console.error('🛑 [AudioEditor] decode failed:', err);
            setLoadError(`Could not decode "${file.name}" — unsupported or corrupt audio.`);
        }
    };

    // ---- Waveform drawing (only the zoomed-in window) ------------------------
    const drawWaveform = () => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        canvas.width = canvas.clientWidth;
        canvas.height = canvas.clientHeight;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#0a0a0a';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        if (!audioBuffer) return;

        const data = audioBuffer.getChannelData(0);
        const total = data.length;
        const vs = Math.floor(view.start * total);
        const ve = Math.max(vs + 1, Math.floor(view.end * total));
        const visible = ve - vs;
        const step = Math.max(1, Math.floor(visible / canvas.width));
        const amp = canvas.height / 2;

        ctx.strokeStyle = '#222';
        ctx.beginPath(); ctx.moveTo(0, amp); ctx.lineTo(canvas.width, amp); ctx.stroke();

        ctx.strokeStyle = '#f4902c';
        ctx.beginPath();
        for (let x = 0; x < canvas.width; x++) {
            let min = 1.0, max = -1.0;
            const base = vs + x * step;
            for (let j = 0; j < step; j++) {
                const d = data[base + j];
                if (d === undefined) break;
                if (d < min) min = d;
                if (d > max) max = d;
            }
            ctx.moveTo(x, (1 + min) * amp);
            ctx.lineTo(x, (1 + max) * amp);
        }
        ctx.stroke();
    };

    React.useEffect(() => { drawWaveform(); }, [audioBuffer, view]);

    // Redraw on container resize so the wave always fills its box.
    React.useEffect(() => {
        const onResize = () => drawWaveform();
        window.addEventListener('resize', onResize);
        return () => window.removeEventListener('resize', onResize);
    });

    // Map full-buffer fraction -> % across the current view (may be <0 or >100).
    const viewSpan = () => (view.end - view.start) || 1;
    const toPct = (pos) => ((pos - view.start) / viewSpan()) * 100;
    const inView = (pos) => pos >= view.start && pos <= view.end;
    const clientXToPos = (clientX) => {
        const rect = canvasRef.current.getBoundingClientRect();
        const frac = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
        return view.start + frac * viewSpan();
    };

    // ---- Zoom ----------------------------------------------------------------
    const zoomAround = (anchor, factor) => {
        const span = viewSpan() * factor;
        if (span >= 1) { setView({ start: 0, end: 1 }); return; }
        if (span < 0.0005) return; // don't over-zoom
        let s = anchor - span / 2;
        let e = anchor + span / 2;
        if (s < 0) { e -= s; s = 0; }
        if (e > 1) { s -= (e - 1); e = 1; }
        setView({ start: Math.max(0, s), end: Math.min(1, e) });
    };
    const zoomIn = () => zoomAround(cursor, 0.5);
    const zoomOut = () => zoomAround(cursor, 2);
    const zoomFit = () => setView({ start: 0, end: 1 });
    const zoomToSelection = () => {
        const pad = (selection.end - selection.start) * 0.15;
        setView({ start: Math.max(0, selection.start - pad), end: Math.min(1, selection.end + pad) });
    };

    // Native non-passive wheel so we can preventDefault the page scroll on zoom.
    React.useEffect(() => {
        const el = waveWrapRef.current;
        if (!el) return;
        const onWheel = (e) => {
            if (!audioBuffer) return;
            e.preventDefault();
            zoomAround(clientXToPos(e.clientX), e.deltaY > 0 ? 1.2 : 0.8);
        };
        el.addEventListener('wheel', onWheel, { passive: false });
        return () => el.removeEventListener('wheel', onWheel);
    }, [audioBuffer, view, cursor]);

    // ---- Cursor + keyboard (I=in, O=out, F=fade) -----------------------------
    const onWaveClick = (e) => {
        if (!audioBuffer) return;
        waveWrapRef.current && waveWrapRef.current.focus();
        setCursor(clientXToPos(e.clientX));
    };

    // Drag an in/out triangle handle along the waveform.
    const dragPoint = (which) => (e) => {
        e.preventDefault(); e.stopPropagation();
        const move = (ev) => {
            const pos = clientXToPos(ev.clientX);
            if (which === 'in') setSelection((s) => ({ ...s, start: Math.max(0, Math.min(pos, s.end - 0.001)) }));
            else setSelection((s) => ({ ...s, end: Math.min(1, Math.max(pos, s.start + 0.001)) }));
        };
        const up = () => { window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', up); };
        window.addEventListener('pointermove', move);
        window.addEventListener('pointerup', up);
    };
    const onKeyDown = (e) => {
        if (!audioBuffer) return;
        const k = e.key.toLowerCase();
        if (k === 'i') { setSelection((s) => ({ ...s, start: Math.min(cursor, s.end - 0.001) })); e.preventDefault(); }
        else if (k === 'o') { setSelection((s) => ({ ...s, end: Math.max(cursor, s.start + 0.001) })); e.preventDefault(); }
        else if (k === 'f') { setFade((f) => !f); e.preventDefault(); }
    };

    // ---- Preview playback (with pitch + fade), animated playhead -------------
    const stopPreview = () => {
        if (previewSrcRef.current) { try { previewSrcRef.current.stop(); } catch (e) {} previewSrcRef.current = null; }
        if (rafRef.current) cancelAnimationFrame(rafRef.current);
        setPlayhead(null);
        setIsPlaying(false);
        setPlayingWhich(null);
    };

    // Play [startFrac..endFrac] of the buffer with the current pitch/fade, animate
    // the playhead. `which` tags which button is lit so it can toggle to stop.
    const playRegion = (startFrac, endFrac, which) => {
        if (!audioBuffer) return;
        if (playingWhich === which) { stopPreview(); return; }
        stopPreview();
        const ctx = getCtx();
        const rate = Math.pow(2, pitchSemi / 12);
        const src = ctx.createBufferSource();
        const gain = ctx.createGain();
        src.buffer = audioBuffer;
        src.playbackRate.value = rate;
        src.connect(gain); gain.connect(ctx.destination);

        const dur = audioBuffer.duration;
        const s = Math.max(0, Math.min(1, startFrac));
        const e = Math.max(s + 0.0005, Math.min(1, endFrac));
        const startSec = s * dur;
        const lenSec = (e - s) * dur;
        const playSec = lenSec / rate;
        const now = ctx.currentTime;
        if (fade) {
            const f = Math.min(0.03, playSec * 0.2);
            gain.gain.setValueAtTime(0.0001, now);
            gain.gain.exponentialRampToValueAtTime(1, now + f);
            gain.gain.setValueAtTime(1, Math.max(now + f, now + playSec - f));
            gain.gain.exponentialRampToValueAtTime(0.0001, now + playSec);
        }
        src.start(now, startSec, lenSec);
        src.onended = () => stopPreview();
        previewSrcRef.current = src;
        setIsPlaying(true);
        setPlayingWhich(which);

        const t0 = performance.now();
        const tick = () => {
            const frac = (performance.now() - t0) / 1000 / playSec;
            if (frac >= 1) { setPlayhead(null); return; }
            setPlayhead(s + frac * (e - s));
            rafRef.current = requestAnimationFrame(tick);
        };
        rafRef.current = requestAnimationFrame(tick);
    };

    // The three transport start points.
    const playFromIn = () => playRegion(selection.start, selection.end, 'in');
    const playFromCursor = () => playRegion(cursor, cursor < selection.end ? selection.end : 1, 'cursor');
    const playFromSevenEighths = () => playRegion(selection.start + 0.875 * (selection.end - selection.start), selection.end, 'seven');
    React.useEffect(() => () => stopPreview(), []);

    // ---- Assign the current slice to the selected pad ------------------------
    const assignToPad = () => {
        if (!audioBuffer) return;
        const ctx = getCtx();
        const total = audioBuffer.length;
        const s = Math.max(0, Math.min(total - 1, Math.floor(selection.start * total)));
        const e = Math.max(s + 1, Math.min(total, Math.floor(selection.end * total)));
        const len = e - s;
        const sliced = ctx.createBuffer(audioBuffer.numberOfChannels, len, audioBuffer.sampleRate);
        for (let ch = 0; ch < audioBuffer.numberOfChannels; ch++) {
            sliced.copyToChannel(audioBuffer.getChannelData(ch).subarray(s, e), ch);
        }
        const name = fileName || 'slice';
        window.oaSetDrumSample(selectedPad, sliced, {
            loop: autoLoop, fade, pitch: Math.pow(2, pitchSemi / 12), name, folder: loadedFolder || '',
        });
        if (mqttPublish) mqttPublish(`OpenAir/Gui/DrumKit/${selectedPad}/sample`, { name, folder: loadedFolder || '' });
        setSamples((list) => {
            const entry = { name, padIdx: selectedPad, padName: padName(selectedPad), loop: autoLoop, fade };
            const next = list.filter((x) => x.padIdx !== selectedPad);
            next.push(entry);
            next.sort((a, b) => a.padIdx - b.padIdx);
            return next;
        });
    };

    // Pitch wheel writes straight through to the selected pad's live sample.
    const onPitch = (semi) => {
        setPitchSemi(semi);
        if (window.oaUpdateDrumSample) window.oaUpdateDrumSample(selectedPad, { pitch: Math.pow(2, semi / 12) });
    };
    // When you pick a different pad, adopt that pad's current pitch.
    React.useEffect(() => {
        const en = window.OA_DRUM_SAMPLES && window.OA_DRUM_SAMPLES[selectedPad];
        setPitchSemi(en && en.pitch ? Math.round(12 * Math.log2(en.pitch)) : 0);
    }, [selectedPad]);

    const btn = (extra) => ({ background: '#333', color: '#ccc', border: '1px solid #444', padding: '5px 10px', cursor: 'pointer', borderRadius: '3px', fontSize: '12px', ...extra });

    return (
        <div
            onDragOver={(e) => { e.preventDefault(); if (!dragOver) setDragOver(true); }}
            onDragLeave={(e) => { if (e.currentTarget === e.target) setDragOver(false); }}
            onDrop={(e) => {
                e.preventDefault();
                setDragOver(false);
                const f = e.dataTransfer.files && e.dataTransfer.files[0];
                if (f) handleFile(f);
            }}
            style={{ padding: '20px', backgroundColor: 'rgba(18,18,18,0.28)', backdropFilter: 'blur(6px)', WebkitBackdropFilter: 'blur(6px)', borderRadius: '4px', color: '#fff', border: dragOver ? '1px dashed #f4902c' : '1px solid #333', width: '100%', boxSizing: 'border-box', position: 'relative' }}
        >
            {dragOver && (
                <div style={{ position: 'absolute', inset: 0, background: 'rgba(244,144,44,0.12)', border: '2px dashed #f4902c', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 5, pointerEvents: 'none', fontSize: '14px', color: '#f4902c', fontWeight: 'bold' }}>
                    Drop audio file to load
                </div>
            )}
            <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', color: '#ccc' }}>{label}</h3>
            {loadError && (
                <div style={{ background: '#3a1a1a', border: '1px solid #a33', borderRadius: '3px', padding: '6px 10px', fontSize: '11px', color: '#f88', marginBottom: '8px' }}>
                    ⚠️ {loadError}
                </div>
            )}

            {/* Top row: load, play, zoom */}
            <div style={{ display: 'flex', gap: '8px', marginBottom: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                <button onClick={() => { if (window.SoundBrowse) setBrowsing(true); else fileInputRef.current && fileInputRef.current.click(); }} style={btn({ background: '#f4902c', color: '#111', border: 'none', fontWeight: 'bold' })}>📁 Browse…</button>
                <input ref={fileInputRef} type="file" accept="audio/*,.mp3,.wav,.wave,.aif,.aiff,.aac,.m4a,.ogg,.oga,.flac,.opus" style={{ display: 'none' }} onChange={(e) => handleFile(e.target.files[0])} />
                <button onClick={playFromIn} disabled={!audioBuffer} title="Play from the in point (I)" style={btn({ background: playingWhich === 'in' ? '#c00' : '#388e3c', color: '#fff', cursor: audioBuffer ? 'pointer' : 'not-allowed', fontWeight: 'bold', border: 'none' })}>
                    {playingWhich === 'in' ? '■' : '►'} In
                </button>
                <button onClick={playFromCursor} disabled={!audioBuffer} title="Play from the cursor" style={btn({ background: playingWhich === 'cursor' ? '#c00' : '#333', color: '#fff', cursor: audioBuffer ? 'pointer' : 'not-allowed' })}>
                    {playingWhich === 'cursor' ? '■' : '►'} Cursor
                </button>
                <button onClick={playFromSevenEighths} disabled={!audioBuffer} title="Play the last ⅛ of the loop (checks the loop tail)" style={btn({ background: playingWhich === 'seven' ? '#c00' : '#333', color: '#fff', cursor: audioBuffer ? 'pointer' : 'not-allowed' })}>
                    {playingWhich === 'seven' ? '■' : '►'} ⅞
                </button>
                <div style={{ width: '1px', height: '20px', background: '#444' }} />
                <span style={{ fontSize: '10px', color: '#888' }}>ZOOM</span>
                <button onClick={zoomOut} disabled={!audioBuffer} style={btn()}>−</button>
                <button onClick={zoomIn} disabled={!audioBuffer} style={btn()}>+</button>
                <button onClick={zoomToSelection} disabled={!audioBuffer} style={btn()}>Sel</button>
                <button onClick={zoomFit} disabled={!audioBuffer} style={btn()}>Fit</button>
                <div style={{ flexGrow: 1 }} />
                <span style={{ fontSize: '12px', color: '#666' }}>{audioBuffer ? `${audioBuffer.duration.toFixed(2)}s` : 'No audio loaded'}</span>
            </div>

            {/* Waveform + overlays (focusable for I/O/F keys) */}
            <div
                ref={waveWrapRef}
                tabIndex={0}
                onKeyDown={onKeyDown}
                onPointerDown={onWaveClick}
                style={{ width: '100%', height: '150px', backgroundColor: '#0a0a0a', border: '1px solid #444', position: 'relative', outline: 'none', cursor: audioBuffer ? 'text' : 'default' }}
            >
                <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />

                {!audioBuffer && (
                    <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#555', fontSize: '12px', pointerEvents: 'none' }}>
                        Drop an audio file here, or use the picker above
                    </div>
                )}

                {/* Selection region (in..out) */}
                {audioBuffer && (
                    <div style={{
                        position: 'absolute', top: 0, height: '100%',
                        left: `${Math.max(0, toPct(selection.start))}%`,
                        width: `${Math.max(0, Math.min(100, toPct(selection.end)) - Math.max(0, toPct(selection.start)))}%`,
                        backgroundColor: 'rgba(244, 144, 44, 0.18)',
                        borderLeft: inView(selection.start) ? '2px solid #f4902c' : 'none',
                        borderRight: inView(selection.end) ? '2px solid #f4902c' : 'none',
                        pointerEvents: 'none',
                    }} />
                )}
                {/* In / Out triangle handles — drag along the waveform */}
                {audioBuffer && inView(selection.start) && (
                    <div onPointerDown={dragPoint('in')} title="In point — drag"
                        style={{ position: 'absolute', bottom: 0, left: `${toPct(selection.start)}%`, transform: 'translateX(-50%)', width: 0, height: 0, borderLeft: '9px solid transparent', borderRight: '9px solid transparent', borderBottom: '13px solid #4caf50', cursor: 'ew-resize', zIndex: 7 }} />
                )}
                {audioBuffer && inView(selection.end) && (
                    <div onPointerDown={dragPoint('out')} title="Out point — drag"
                        style={{ position: 'absolute', bottom: 0, left: `${toPct(selection.end)}%`, transform: 'translateX(-50%)', width: 0, height: 0, borderLeft: '9px solid transparent', borderRight: '9px solid transparent', borderBottom: '13px solid #f44336', cursor: 'ew-resize', zIndex: 7 }} />
                )}
                {/* Cursor */}
                {audioBuffer && inView(cursor) && (
                    <div style={{ position: 'absolute', top: 0, height: '100%', left: `${toPct(cursor)}%`, width: '1px', background: '#8ab4f8', pointerEvents: 'none' }} />
                )}
                {/* Playhead */}
                {audioBuffer && playhead != null && inView(playhead) && (
                    <div style={{ position: 'absolute', top: 0, height: '100%', left: `${toPct(playhead)}%`, width: '2px', background: '#fff', pointerEvents: 'none' }} />
                )}
                {fade && audioBuffer && (
                    <div style={{ position: 'absolute', top: '4px', right: '6px', fontSize: '10px', color: '#f4902c', fontWeight: 'bold', pointerEvents: 'none' }}>FADE</div>
                )}
            </div>

            {audioBuffer && (
                <div style={{ fontSize: '10px', color: '#777', marginTop: '4px' }}>
                    Click the wave to place the cursor, then <b style={{ color: '#8ab4f8' }}>I</b> = in point · <b style={{ color: '#8ab4f8' }}>O</b> = out point · <b style={{ color: '#8ab4f8' }}>F</b> = fade · wheel/±  = zoom
                </div>
            )}

            {/* In / out readout (drag the triangles on the waveform to move them) */}
            {audioBuffer && (
                <div style={{ display: 'flex', gap: '16px', marginTop: '8px', fontSize: '11px', color: '#aaa' }}>
                    <span>IN <b style={{ color: '#4caf50' }}>{(selection.start * audioBuffer.duration).toFixed(3)}s</b></span>
                    <span>OUT <b style={{ color: '#f44336' }}>{(selection.end * audioBuffer.duration).toFixed(3)}s</b></span>
                    <span>LEN <b style={{ color: '#f4902c' }}>{((selection.end - selection.start) * audioBuffer.duration).toFixed(3)}s</b></span>
                </div>
            )}

            {/* Assign row */}
            {audioBuffer && (
                <div style={{ display: 'flex', gap: '10px', marginTop: '12px', alignItems: 'center', flexWrap: 'wrap', borderTop: '1px solid #333', paddingTop: '10px' }}>
                    <span style={{ fontSize: '11px', color: '#aaa' }}>PAD</span>
                    <select value={selectedPad} onChange={(e) => setSelectedPad(Number(e.target.value))}
                        style={{ background: '#000', color: '#f4902c', border: '1px solid #444', padding: '4px', fontSize: '12px', borderRadius: '3px' }}>
                        {KIT.map((k, i) => (
                            <option key={i} value={i}>{i + 1}. {k.name}{window.OA_DRUM_SAMPLES[i] ? ' •' : ''}</option>
                        ))}
                    </select>
                    <label style={{ fontSize: '11px', color: '#ccc', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <input type="checkbox" checked={autoLoop} onChange={(e) => setAutoLoop(e.target.checked)} /> Auto-loop
                    </label>
                    <label style={{ fontSize: '11px', color: '#ccc', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <input type="checkbox" checked={fade} onChange={(e) => setFade(e.target.checked)} /> Fade
                    </label>
                    <button onClick={assignToPad} style={btn({ background: '#f4902c', color: '#111', fontWeight: 'bold', border: 'none', padding: '6px 14px' })}>
                        ⭳ Assign to Pad
                    </button>
                </div>
            )}

            {/* Pitch wheel — active once the selected pad has a sample */}
            {audioBuffer && (
                <div style={{ display: 'flex', gap: '10px', marginTop: '10px', alignItems: 'center', opacity: selectedHasSample ? 1 : 0.4 }}>
                    <span style={{ fontSize: '11px', color: '#aaa', width: '90px' }}>PITCH · {padName(selectedPad)}</span>
                    <input type="range" min="-12" max="12" step="1" value={pitchSemi} disabled={!selectedHasSample}
                        onChange={(e) => onPitch(Number(e.target.value))}
                        style={{ flex: 1 }} />
                    <span style={{ fontSize: '12px', color: '#f4902c', fontWeight: 'bold', width: '54px', textAlign: 'right' }}>
                        {pitchSemi > 0 ? '+' : ''}{pitchSemi} st
                    </span>
                </div>
            )}

            {/* Captured samples list */}
            {samples.length > 0 && (
                <div style={{ marginTop: '12px', borderTop: '1px solid #333', paddingTop: '8px' }}>
                    <div style={{ fontSize: '11px', color: '#888', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '6px' }}>
                        Captured Samples
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        {samples.map((s) => (
                            <div key={s.padIdx} onClick={() => setSelectedPad(s.padIdx)}
                                style={{ display: 'flex', alignItems: 'center', gap: '8px', background: s.padIdx === selectedPad ? '#33291a' : '#242424', border: '1px solid #3a3a3a', borderRadius: '3px', padding: '4px 8px', cursor: 'pointer' }}>
                                <button onClick={(e) => { e.stopPropagation(); window.oaTriggerDrum && window.oaTriggerDrum(s.padIdx, 1); }}
                                    style={btn({ padding: '2px 8px', background: '#f4902c', color: '#111', border: 'none', fontWeight: 'bold' })}>►</button>
                                <span style={{ fontSize: '12px', color: '#f4902c', width: '78px' }}>{s.padName}</span>
                                <span style={{ fontSize: '12px', color: '#ccc', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.name}</span>
                                {s.loop && <span style={{ fontSize: '9px', color: '#111', background: '#8ab4f8', padding: '1px 4px', borderRadius: '2px', fontWeight: 'bold' }}>LOOP</span>}
                                {s.fade && <span style={{ fontSize: '9px', color: '#111', background: '#f4902c', padding: '1px 4px', borderRadius: '2px', fontWeight: 'bold' }}>FADE</span>}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {browsing && window.SoundBrowse && (
                <window.SoundBrowse
                    targetLabel="Wave editor"
                    onClose={() => setBrowsing(false)}
                    onChoose={(file, meta) => { handleFile(file, meta && meta.folder); setBrowsing(false); }}
                />
            )}
        </div>
    );
};
window.AudioEditor = AudioEditor;
