const Sampler = ({ label = "Drum Sampler", centerVelocity = 100, edgeVelocity = 10, onHit = null }) => {
    // Shared drum kit — the SAME 16 voices the Sequencer uses (DrumKit.js).
    const KIT = window.OA_DRUM_KIT || [];

    // Per-pad loaded-sample file name (for display); null = uses the synth voice.
    // The decoded audio lives in window.OA_DRUM_SAMPLES so the Sequencer plays it
    // too. Seed from that shared store so pads loaded before a remount still show.
    const [sampleNames, setSampleNames] = React.useState(() =>
        Array(16).fill(null).map((_, i) => {
            const e = window.OA_DRUM_SAMPLES && window.OA_DRUM_SAMPLES[i];
            return e ? (e.name || '(loaded)') : null;
        }));

    // Side-car value per pad: velocity (0-100) of the most recent hit. Drives
    // playback volume AND the pad's visual glow.
    const [velocities, setVelocities] = React.useState(Array(16).fill(0));

    // Hidden file inputs, one per pad (fallback when the Sound Browse window
    // isn't available). ALT+press normally opens the custom Sound Browse modal.
    const fileInputs = React.useRef([]);
    const [browsePad, setBrowsePad] = React.useState(null);
    // "Load to other pad" mode: the next pad clicked receives this sample.
    const [pendingAssign, setPendingAssign] = React.useState(null); // { file, meta }

    // Remembered assignments from retained MQTT: { idx: {name, folder} }. Lets the
    // kit revert (labels immediately; audio via Restore) after a reload.
    const mqttMessages = window.useMqttMessages ? window.useMqttMessages() : {};
    const kitMeta = React.useMemo(() => {
        const m = {};
        for (let i = 0; i < 16; i++) {
            const raw = mqttMessages[`OpenAir/Gui/DrumKit/${i}/sample`];
            if (raw) { try { const o = JSON.parse(raw); if (o && o.name) m[i] = o; } catch (e) {} }
        }
        return m;
    }, [mqttMessages]);
    const [restoreMsg, setRestoreMsg] = React.useState('');
    const missingCount = Object.keys(kitMeta).filter((i) => !(window.OA_DRUM_SAMPLES && window.OA_DRUM_SAMPLES[i])).length;
    const restoreSounds = async () => {
        if (!window.oaRestoreKit) return;
        setRestoreMsg('restoring…');
        const res = await window.oaRestoreKit(kitMeta);
        if (res.ok) {
            setRestoreMsg(`restored ${res.restored}`);
            setSampleNames((prev) => { const n = [...prev]; for (let i = 0; i < 16; i++) { const e = window.OA_DRUM_SAMPLES[i]; if (e) n[i] = e.name || '(loaded)'; } return n; });
        } else setRestoreMsg(res.reason === 'no-folder' ? 'pick a folder first' : 'permission denied');
        setTimeout(() => setRestoreMsg(''), 2500);
    };

    // The standard MPC layout is bottom-left to top-right:
    // 13 14 15 16
    // 9  10 11 12
    // 5  6  7  8
    // 1  2  3  4
    const layout = [13, 14, 15, 16, 9, 10, 11, 12, 5, 6, 7, 8, 1, 2, 3, 4];

    // Load a sample onto a pad: decode to an AudioBuffer in the SHARED store so
    // both this pad and the Sequencer's matching track play it.
    const mqttPublish = window.useMqttPublish ? window.useMqttPublish() : null;
    // Persist which sample (name + source folder) is on a kit voice, retained.
    const publishSample = (idx, name, folder) => {
        if (mqttPublish) mqttPublish(`OpenAir/Gui/DrumKit/${idx}/sample`, { name: name || '', folder: folder || '' });
    };

    const handleFile = async (index, file, meta) => {
        if (!file) return;
        try {
            const arrayBuf = await file.arrayBuffer();
            const ctx = window.oaAudioCtx();
            const audioBuf = await window.oaDecodeAudio(ctx, arrayBuf);
            window.oaSetDrumSample(index, audioBuf, { name: file.name });
            setSampleNames((prev) => { const n = [...prev]; n[index] = file.name; return n; });
            publishSample(index, file.name, meta && meta.folder);
        } catch (e) {
            console.error('🛑 [Sampler] Could not decode audio:', e);
        }
    };

    // Position-sensitive velocity: centre of the pad = centerVelocity, the edge =
    // edgeVelocity, smooth radial falloff (normalized by the inscribed radius).
    const computeVelocity = (e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const cx = rect.left + rect.width / 2;
        const cy = rect.top + rect.height / 2;
        const dx = e.clientX - cx;
        const dy = e.clientY - cy;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const radius = (Math.min(rect.width, rect.height) / 2) || 1;
        const d = Math.min(dist / radius, 1);
        const v = centerVelocity + (edgeVelocity - centerVelocity) * d;
        return Math.round(Math.max(0, Math.min(100, v)));
    };

    // A pad was struck: compute velocity, store it, trigger the drum (sample or
    // synth) at a volume scaled by the velocity, notify.
    // Broadcast a hit so the Sequencer can record it (idx + velocity 0-100).
    const emitHit = (idx, velocity) => {
        window.dispatchEvent(new CustomEvent('oa-drum-hit', { detail: { idx, velocity } }));
    };

    const hitPad = (e, idx) => {
        const velocity = computeVelocity(e);
        setVelocities((prev) => { const n = [...prev]; n[idx] = velocity; return n; });
        if (window.oaTriggerDrum) window.oaTriggerDrum(idx, velocity / 100);
        if (typeof onHit === 'function') onHit(idx + 1, velocity);
        emitHit(idx, velocity);
        return velocity;
    };

    // Pad <button> elements (so keyboard triggers can flash their glow) plus a
    // visibility gate so number-pad keys only fire when this Sampler is on screen.
    const padButtons = React.useRef([]);
    const rootRef = React.useRef(null);
    const visibleRef = React.useRef(false);

    // Restart the velocity glow on a pad element (bright → fades over sound length).
    const startGlow = (el, idx, i) => {
        if (!el) return;
        const entry = window.OA_DRUM_SAMPLES[idx];
        const durMs = (entry && entry.buffer) ? Math.max(120, Math.min(entry.buffer.duration * 1000, 5000)) : 180;
        el.style.setProperty('--gi', i);
        el.style.animation = 'none';
        void el.offsetWidth;            // reflow → restart on rapid hits
        el.style.animation = `oaPadGlow ${durMs}ms ease-out`;
    };

    // Trigger a pad from the keyboard (full velocity), with a brief press + glow.
    const triggerPadKey = (idx) => {
        setVelocities((prev) => { const n = [...prev]; n[idx] = 100; return n; });
        if (window.oaTriggerDrum) window.oaTriggerDrum(idx, 1);
        if (typeof onHit === 'function') onHit(idx + 1, 100);
        emitHit(idx, 100);
        const el = padButtons.current[idx];
        if (el) {
            el.style.transform = 'scale(0.95)';
            el.style.filter = 'brightness(1.5)';
            startGlow(el, idx, 1);
            setTimeout(() => { if (el) { el.style.transform = 'scale(1)'; el.style.filter = 'none'; } }, 90);
        }
    };

    // Number-pad → pad mapping (only while this Sampler is on screen). The 3×3
    // numpad maps spatially to the bottom-left 3×3 of the MPC pads:
    //   1 2 3 → pads 1 2 3   ·   4 5 6 → pads 5 6 7   ·   7 8 9 → pads 9 10 11
    const NUMKEY_TO_PADNUM = { 1: 1, 2: 2, 3: 3, 4: 5, 5: 6, 6: 7, 7: 9, 8: 10, 9: 11 };

    React.useEffect(() => {
        const el = rootRef.current;
        if (!el || typeof IntersectionObserver === 'undefined') return;
        const io = new IntersectionObserver(([en]) => { visibleRef.current = en.isIntersecting; }, { threshold: 0.3 });
        io.observe(el);
        return () => io.disconnect();
    }, []);

    React.useEffect(() => {
        const onKey = (e) => {
            if (!visibleRef.current) return;
            const t = e.target;
            if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT' || t.isContentEditable)) return;
            const m = /^(?:Numpad|Digit)([1-9])$/.exec(e.code || '');
            if (!m) return;
            const padNum = NUMKEY_TO_PADNUM[parseInt(m[1], 10)];
            if (!padNum) return;
            e.preventDefault();
            triggerPadKey(padNum - 1);
        };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, []);

    // Glow a pad whenever the Sequencer plays that voice (intensity = step velocity).
    // Imperative only (no state) so 16th-note flashes don't churn React renders.
    React.useEffect(() => {
        const onPlay = (e) => {
            const idx = e.detail && e.detail.idx;
            if (idx == null) return;
            const el = padButtons.current[idx];
            if (!el) return;
            const i = Math.max(0, Math.min(1, (e.detail.velocity || 0) / 100));
            el.style.filter = `brightness(${0.9 + 0.5 * i})`;
            startGlow(el, idx, i);
            setTimeout(() => { if (el) el.style.filter = 'none'; }, 120);
        };
        window.addEventListener('oa-drum-play', onPlay);
        return () => window.removeEventListener('oa-drum-play', onPlay);
    }, []);

    // Esc cancels "Load to other pad" mode.
    React.useEffect(() => {
        if (!pendingAssign) return;
        const onEsc = (e) => { if (e.key === 'Escape') setPendingAssign(null); };
        window.addEventListener('keydown', onEsc);
        return () => window.removeEventListener('keydown', onEsc);
    }, [pendingAssign]);

    return (
        <div ref={rootRef} style={{ padding: '25px', backgroundColor: '#1e1e1e', borderRadius: '4px', color: '#fff', border: '1px solid #333', display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%', boxSizing: 'border-box' }}>
            {/* Velocity glow: bright on strike (scaled by --gi), fades over the sound's length. */}
            <style>{`
                @keyframes oaPadGlow {
                    from {
                        box-shadow: 0 0 calc(12px + var(--gi, 0.5) * 48px) calc(3px + var(--gi, 0.5) * 16px) rgba(244, 144, 44, calc(0.5 + var(--gi, 0.5) * 0.5));
                    }
                    to {
                        box-shadow: 0 0 0 0 rgba(244, 144, 44, 0);
                    }
                }
            `}</style>
            <h3 style={{ margin: '0 0 20px 0', fontSize: '18px', color: '#ccc', textAlign: 'center', textTransform: 'uppercase', letterSpacing: '1px' }}>{label}</h3>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '18px', justifyContent: 'center', padding: '18px', background: '#0a0a0a', border: '1px solid #111', borderRadius: '8px' }}>
                {layout.map((padNum) => {
                    const idx = padNum - 1;
                    const name = (KIT[idx] && KIT[idx].name) || `Pad ${padNum}`;
                    const hasSample = !!(window.OA_DRUM_SAMPLES && window.OA_DRUM_SAMPLES[idx] && window.OA_DRUM_SAMPLES[idx].buffer);
                    const remembered = kitMeta[idx];        // known from MQTT but not (yet) loaded
                    const vel = velocities[idx];            // side-car value (0-100)
                    const intensity = vel / 100;

                    // Every pad plays a sound; a loaded custom sample reads brighter
                    // orange, a synth-voice pad reads darker. Resting glow reflects
                    // the last hit's velocity.
                    const baseColor = hasSample ? '#f4902c' : '#3a3a3a';
                    // Resting shadow only — the velocity glow is a transient CSS
                    // animation (oaPadGlow) that lasts exactly as long as the sound
                    // plays, then fades to this dark resting state.
                    const restShadow = hasSample ? '0 4px 8px rgba(0,0,0,0.4)' : 'inset 0 1px 3px rgba(0,0,0,0.6)';

                    return (
                        <div key={padNum} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            <button
                                ref={(el) => { padButtons.current[idx] = el; }}
                                title={hasSample ? `${name} — sample: ${(window.OA_DRUM_SAMPLES[idx] && window.OA_DRUM_SAMPLES[idx].name) || sampleNames[idx]}\nALT+click to replace` : (remembered ? `${name} — remembered: ${remembered.name}\n(Restore to re-load, or ALT+click to pick)` : `${name} — synth voice\nALT+click to load a sample`)}
                                onPointerDown={(e) => {
                                    // "Load to other pad": this click assigns the pending sample here.
                                    if (pendingAssign) {
                                        e.preventDefault();
                                        handleFile(idx, pendingAssign.file, pendingAssign.meta);
                                        setPendingAssign(null);
                                        return;
                                    }
                                    // ALT+press opens Sound Browse (or the native
                                    // picker as a fallback) instead of playing.
                                    if (e.altKey) {
                                        e.preventDefault();
                                        if (window.SoundBrowse) setBrowsePad(idx);
                                        else { const input = fileInputs.current[idx]; if (input) input.click(); }
                                        return;
                                    }
                                    const v = hitPad(e, idx);
                                    const i = v / 100;
                                    const el = e.currentTarget;
                                    el.style.transform = 'scale(0.95)';
                                    el.style.filter = `brightness(${0.9 + 0.7 * i})`;
                                    startGlow(el, idx, i);
                                }}
                                onPointerUp={(e) => {
                                    e.currentTarget.style.transform = 'scale(1)';
                                    e.currentTarget.style.filter = 'none';
                                }}
                                onPointerLeave={(e) => {
                                    e.currentTarget.style.transform = 'scale(1)';
                                    e.currentTarget.style.filter = 'none';
                                }}
                                style={{
                                    position: 'relative',
                                    width: '120px', height: '120px',
                                    backgroundColor: baseColor,
                                    border: '1px solid #000',
                                    borderTop: '1px solid #555',
                                    borderLeft: '1px solid #444',
                                    borderRadius: '6px',
                                    cursor: 'pointer',
                                    boxShadow: restShadow,
                                    color: hasSample ? '#000' : '#ccc',
                                    fontWeight: 'bold',
                                    display: 'flex', flexDirection: 'column',
                                    alignItems: 'center', justifyContent: 'center',
                                    textAlign: 'center', padding: '4px',
                                    transition: 'transform 0.05s, background-color 0.05s, filter 0.05s',
                                    outline: 'none',
                                    touchAction: 'none'
                                }}
                            >
                                {/* Pad name = shared kit / Sequencer track name */}
                                <span style={{ fontSize: '15px', lineHeight: 1.1, wordBreak: 'break-word' }}>{name}</span>

                                {/* Tiny pad number, corner */}
                                <span style={{ position: 'absolute', bottom: '4px', left: '6px', fontSize: '9px', fontWeight: 'bold', opacity: 0.5 }}>
                                    {padNum}
                                </span>

                                {/* SMP badge when a custom sample is loaded; ○ when only remembered (from MQTT) */}
                                {hasSample ? (
                                    <span style={{ position: 'absolute', bottom: '4px', right: '6px', fontSize: '8px', fontWeight: 'bold', opacity: 0.7, letterSpacing: '0.5px' }}>
                                        SMP
                                    </span>
                                ) : (remembered && (
                                    <span title={`Remembered: ${remembered.name}`} style={{ position: 'absolute', bottom: '3px', right: '5px', fontSize: '10px', fontWeight: 'bold', color: '#8ab4f8', opacity: 0.8 }}>
                                        ○
                                    </span>
                                ))}

                                {/* Side-car velocity readout */}
                                {vel > 0 && (
                                    <span style={{ position: 'absolute', top: '4px', right: '6px', fontSize: '10px', fontWeight: 'bold', color: hasSample ? '#3a1f00' : '#f4902c', opacity: 0.9 }}>
                                        {vel}
                                    </span>
                                )}
                            </button>

                            {/* Hidden per-pad file input — only reachable via ALT+press */}
                            <input
                                ref={(el) => { fileInputs.current[idx] = el; }}
                                type="file"
                                accept="audio/*"
                                style={{ display: 'none' }}
                                onChange={(e) => handleFile(idx, e.target.files[0])}
                            />
                        </div>
                    );
                })}
            </div>

            {missingCount > 0 && (
                <div style={{ marginTop: '10px', textAlign: 'center' }}>
                    <button onClick={restoreSounds} title="Re-load the samples remembered on these pads (from MQTT) using the saved folder"
                        style={{ background: '#8ab4f8', color: '#111', border: 'none', borderRadius: '3px', padding: '5px 12px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer' }}>
                        ↻ Restore {missingCount} sample{missingCount > 1 ? 's' : ''}{restoreMsg ? ` · ${restoreMsg}` : ''}
                    </button>
                </div>
            )}

            <div style={{ marginTop: '14px', fontSize: '10px', color: '#666', textTransform: 'uppercase', letterSpacing: '0.5px', textAlign: 'center' }}>
                Velocity: centre {centerVelocity}% · edge {edgeVelocity}% (sets volume) · <b>ALT+click</b> a pad to browse sounds
            </div>

            {browsePad != null && window.SoundBrowse && (
                <window.SoundBrowse
                    targetLabel={(KIT[browsePad] && KIT[browsePad].name) || `Pad ${browsePad + 1}`}
                    onClose={() => setBrowsePad(null)}
                    onChoose={(file, meta) => { handleFile(browsePad, file, meta); setBrowsePad(null); }}
                    onChooseOther={(file, meta) => { setBrowsePad(null); setPendingAssign({ file, meta }); }}
                />
            )}

            {pendingAssign && (
                <div style={{ position: 'fixed', top: '12px', left: '50%', transform: 'translateX(-50%)', zIndex: 10001, background: '#8ab4f8', color: '#111', padding: '8px 16px', borderRadius: '4px', fontSize: '13px', fontWeight: 'bold', boxShadow: '0 4px 16px rgba(0,0,0,0.5)' }}>
                    👆 Click a pad to assign "{pendingAssign.meta && pendingAssign.meta.name}" — Esc to cancel
                </div>
            )}
        </div>
    );
};
window.Sampler = Sampler;
