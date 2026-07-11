/**
 * PadBrowse.jsx — "Pad Browser" window. Pick a folder; each of the 16 kit voices
 * gets a mini waveform "stack" of the matching samples found in the tree (Kick,
 * Snare, … Conga). Arrow Left/Right moves the focused pad; Up/Down cycles that
 * pad's sound (loading it live, so you can shuffle sounds while the sequence
 * plays). Each cell also has ▲/▼ buttons.
 */
const PAD_AUDIO_RE = /\.(mp3|wav|wave|aif|aiff|aac|m4a|ogg|oga|flac|opus)$/i;

// Per-kit-voice match keywords (lowercased substrings on the filename).
const PAD_KEYWORDS = {
    0: ['kick', 'bd', 'bassdrum', 'bass drum'],
    1: ['snare', 'sd', 'snr'],
    2: ['hihat', 'hi-hat', 'hh', 'hat'],
    3: ['perc', 'prc'],
    4: ['clap', 'clp', 'handclap'],
    5: ['rim', 'rimshot', 'rs'],
    6: ['tomlo', 'low tom', 'floor', 'tom', 'lt'],
    7: ['tommid', 'mid tom', 'tom', 'mt'],
    8: ['tomhi', 'hi tom', 'high tom', 'tom', 'ht'],
    9: ['cymbal', 'cym', 'crash'],
    10: ['ride', 'rd'],
    11: ['cowbell', 'cowbel', 'cowb', 'cow', 'cb'],
    12: ['conga', 'cng', 'cga', 'cong'],
    13: ['clave', 'clav', 'clv'],
    14: ['shaker', 'shake', 'shk'],
    15: ['fx', 'sfx', 'effect', 'riser', 'sweep'],
};

const padGather = async (handle, prefix, out, depth) => {
    if (depth > 12 || out.length >= 40000) return;
    const subdirs = [];
    for await (const [n, h] of handle.entries()) {
        if (out.length >= 40000) break;
        if (h.kind === 'directory') subdirs.push([n, h]);
        else if (PAD_AUDIO_RE.test(n)) out.push({ name: n, handle: h, sub: prefix });
    }
    for (const [n, h] of subdirs) { if (out.length >= 40000) break; await padGather(h, prefix ? `${prefix}/${n}` : n, out, depth + 1); }
};

// One pad cell: draws the current entry's waveform.
const PadCell = ({ voice, idx, stack, selIdx, focused, onFocus, onCycle }) => {
    const canvasRef = React.useRef(null);
    const entry = stack[selIdx];
    React.useEffect(() => {
        let cancelled = false;
        const c = canvasRef.current; if (!c) return;
        c.width = c.clientWidth || 130; c.height = c.clientHeight || 40;
        const cx = c.getContext('2d'); cx.fillStyle = '#0a0a0a'; cx.fillRect(0, 0, c.width, c.height);
        if (!entry) return;
        (async () => {
            try {
                const file = entry.file || await entry.handle.getFile();
                const buf = await window.oaDecodeAudio(window.oaAudioCtx(), await file.arrayBuffer());
                if (cancelled || !canvasRef.current) return;
                const data = buf.getChannelData(0);
                const step = Math.max(1, Math.ceil(data.length / c.width));
                const amp = c.height / 2;
                cx.strokeStyle = '#f4902c'; cx.beginPath();
                for (let x = 0; x < c.width; x++) { let mn = 1, mx = -1; for (let j = 0; j < step; j++) { const d = data[x * step + j]; if (d === undefined) break; if (d < mn) mn = d; if (d > mx) mx = d; } cx.moveTo(x, (1 + mn) * amp); cx.lineTo(x, (1 + mx) * amp); }
                cx.stroke();
            } catch (e) {}
        })();
        return () => { cancelled = true; };
    }, [entry]);
    return (
        <div onClick={onFocus}
            style={{ border: focused ? '2px solid #f4902c' : '1px solid #444', borderRadius: '5px', background: focused ? '#2a2018' : '#141414', padding: '5px', cursor: 'pointer', boxSizing: 'border-box' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '3px' }}>
                <span style={{ fontSize: '11px', color: '#f4902c', fontWeight: 'bold' }}>{voice}</span>
                <span style={{ fontSize: '9px', color: '#888' }}>{stack.length ? `${selIdx + 1}/${stack.length}` : '0'}</span>
            </div>
            <canvas ref={canvasRef} style={{ width: '100%', height: '40px', display: 'block', background: '#0a0a0a' }} />
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '3px' }}>
                <button onClick={(e) => { e.stopPropagation(); onFocus(); onCycle(-1); }} disabled={!stack.length} style={{ background: '#333', color: '#ccc', border: '1px solid #444', borderRadius: '3px', width: '20px', cursor: 'pointer', fontSize: '11px' }}>▲</button>
                <button onClick={(e) => { e.stopPropagation(); onFocus(); onCycle(1); }} disabled={!stack.length} style={{ background: '#333', color: '#ccc', border: '1px solid #444', borderRadius: '3px', width: '20px', cursor: 'pointer', fontSize: '11px' }}>▼</button>
                <span style={{ fontSize: '9px', color: '#bbb', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{entry ? entry.name : (stack.length ? '' : 'no match')}</span>
            </div>
        </div>
    );
};

window.PadBrowse = ({ onClose }) => {
    const KIT = window.OA_DRUM_KIT || [];
    const supportsFS = typeof window.showDirectoryPicker === 'function';
    const [rootHandle, setRootHandle] = React.useState(supportsFS ? (window.OA_SOUND_DIR || null) : null);
    const [stacks, setStacks] = React.useState(() => Array(16).fill(null).map(() => []));
    const [sel, setSel] = React.useState(() => Array(16).fill(0));
    const [focus, setFocus] = React.useState(0);   // layout position 0-15
    const [scanning, setScanning] = React.useState(false);
    const [err, setErr] = React.useState('');
    const publish = window.useMqttPublish ? window.useMqttPublish() : null;

    // MPC layout: 13-16 top row … 1-4 bottom row.
    const layout = [13, 14, 15, 16, 9, 10, 11, 12, 5, 6, 7, 8, 1, 2, 3, 4];
    const stacksRef = React.useRef(stacks); stacksRef.current = stacks;

    const buildStacks = async (handle) => {
        setScanning(true); setErr('');
        const all = [];
        try { await padGather(handle, handle.name || 'root', all, 0); } catch (e) { setErr('Could not read folder.'); }
        const st = Array(16).fill(null).map(() => []);
        all.forEach((f) => {
            const lc = f.name.toLowerCase();
            for (let i = 0; i < 16; i++) if ((PAD_KEYWORDS[i] || []).some((k) => lc.includes(k))) st[i].push(f);
        });
        setStacks(st); setSel(Array(16).fill(0)); setScanning(false);
    };
    React.useEffect(() => { if (rootHandle) buildStacks(rootHandle); }, []);

    const pickFolder = async () => {
        try { const h = await window.showDirectoryPicker(); window.OA_SOUND_DIR = h; if (window.oaIdbSet) window.oaIdbSet('oaRootDir', h).catch(() => {}); setRootHandle(h); buildStacks(h); }
        catch (e) {}
    };

    const loadPadSound = async (idx, entry) => {
        if (!entry) return;
        try {
            const file = entry.file || await entry.handle.getFile();
            const buf = await window.oaDecodeAudio(window.oaAudioCtx(), await file.arrayBuffer());
            const prev = window.OA_DRUM_SAMPLES[idx] || {};
            window.oaSetDrumSample(idx, buf, { name: entry.name, folder: entry.sub || '', pitch: prev.pitch, loop: prev.loop, fade: prev.fade });
            if (publish) publish(`OpenAir/Gui/DrumKit/${idx}/sample`, { name: entry.name, folder: entry.sub || '' });
            if (window.oaTriggerDrum) window.oaTriggerDrum(idx, 1);   // audition
        } catch (e) {}
    };

    const cyclePad = (idx, delta) => {
        const len = stacksRef.current[idx].length; if (!len) return;
        setSel((prev) => {
            const n = [...prev]; n[idx] = ((prev[idx] + delta) % len + len) % len;
            loadPadSound(idx, stacksRef.current[idx][n[idx]]);
            return n;
        });
    };

    // Keyboard: Left/Right move the focused pad; Up/Down cycle its sound.
    React.useEffect(() => {
        const onKey = (e) => {
            if (e.target && e.target.tagName === 'INPUT') return;
            if (e.key === 'ArrowLeft') { setFocus((f) => (f + 15) % 16); e.preventDefault(); }
            else if (e.key === 'ArrowRight') { setFocus((f) => (f + 1) % 16); e.preventDefault(); }
            else if (e.key === 'ArrowUp') { cyclePad(layout[focus] - 1, -1); e.preventDefault(); }
            else if (e.key === 'ArrowDown') { cyclePad(layout[focus] - 1, 1); e.preventDefault(); }
        };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, [focus]);

    return (
        <div onClick={onClose} style={{ position: 'fixed', inset: 0, zIndex: 10000, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'sans-serif' }}>
            <div onClick={(e) => e.stopPropagation()} style={{ width: '740px', maxWidth: '95vw', maxHeight: '90vh', display: 'flex', flexDirection: 'column', background: '#1c1c1c', border: '1px solid #f4902c', borderRadius: '6px', color: '#eee', boxShadow: '0 10px 40px rgba(0,0,0,0.6)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid #333' }}>
                    <h3 style={{ margin: 0, color: '#f4902c', textTransform: 'uppercase', letterSpacing: '1px', fontSize: '15px' }}>Pad Browser</h3>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#888', fontSize: '20px', cursor: 'pointer' }}>×</button>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 16px', borderBottom: '1px solid #2a2a2a', flexWrap: 'wrap' }}>
                    {supportsFS
                        ? <button onClick={pickFolder} style={{ background: '#f4902c', color: '#111', border: 'none', borderRadius: '3px', padding: '6px 12px', fontSize: '13px', fontWeight: 'bold', cursor: 'pointer' }}>📁 Choose folder…</button>
                        : <span style={{ fontSize: '12px', color: '#f55' }}>Pad Browser needs Chrome/Edge (folder access).</span>}
                    <span style={{ fontSize: '11px', color: '#888' }}>{scanning ? 'scanning…' : (rootHandle ? (rootHandle.name || '') : '')} · ← → focus pad · ↑ ↓ swap sound</span>
                    {err && <span style={{ fontSize: '11px', color: '#f88' }}>⚠️ {err}</span>}
                </div>
                <div style={{ padding: '12px', overflowY: 'auto' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
                        {layout.map((padNum, pos) => {
                            const idx = padNum - 1;
                            return (
                                <PadCell key={padNum}
                                    voice={(KIT[idx] && KIT[idx].name) || `Pad ${padNum}`}
                                    idx={idx} stack={stacks[idx]} selIdx={sel[idx]}
                                    focused={focus === pos}
                                    onFocus={() => setFocus(pos)}
                                    onCycle={(d) => cyclePad(idx, d)} />
                            );
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
};
