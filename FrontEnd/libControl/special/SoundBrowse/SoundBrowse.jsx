/**
 * SoundBrowse.jsx — custom "Sound Browse" window (replaces the native file
 * dialog for loading pad samples). Browse a folder as an expandable TREE,
 * auto-preview the first 5s of each file on select, scrub / play / rewind /
 * loop, then Load onto the target pad.
 *
 * Directory tree uses the File System Access API (showDirectoryPicker,
 * Chromium). Where unavailable it falls back to a flat multi-file picker.
 */
const AUDIO_RE = /\.(mp3|wav|wave|aif|aiff|aac|m4a|ogg|oga|flac|opus)$/i;

const sortEntries = (items) =>
    items.sort((a, b) => (a.kind === b.kind ? a.name.localeCompare(b.name) : (a.kind === 'dir' ? -1 : 1)));

// One folder node in the tree. Children are lazily listed on first expand.
const SoundTreeNode = ({ name, handle, depth, defaultOpen, onSelectFile, selectedName, pathPrefix }) => {
    const [open, setOpen] = React.useState(!!defaultOpen);
    const [children, setChildren] = React.useState(null); // null = not loaded yet

    const load = async () => {
        const items = [];
        try {
            for await (const [n, h] of handle.entries()) {
                if (h.kind === 'directory') items.push({ name: n, kind: 'dir', handle: h });
                else if (AUDIO_RE.test(n)) items.push({ name: n, kind: 'file', handle: h });
            }
        } catch (e) { /* unreadable folder */ }
        setChildren(sortEntries(items));
    };

    React.useEffect(() => { if (defaultOpen && children === null) load(); }, []);
    const toggle = () => { const nx = !open; setOpen(nx); if (nx && children === null) load(); };
    const pad = 6 + depth * 14;

    return (
        <div>
            <div onClick={toggle} style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '3px 8px', paddingLeft: `${pad}px`, cursor: 'pointer', fontSize: '13px', color: '#8ab4f8' }}>
                <span style={{ width: '10px', color: '#888' }}>{open ? '▾' : '▸'}</span>
                <span>📁 {name}</span>
            </div>
            {open && children && children.map((c, i) => (
                c.kind === 'dir'
                    ? <SoundTreeNode key={i} name={c.name} handle={c.handle} depth={depth + 1} onSelectFile={onSelectFile} selectedName={selectedName} pathPrefix={`${pathPrefix}/${c.name}`} />
                    : (
                        <div key={i} onClick={() => onSelectFile(c, pathPrefix)}
                            style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '3px 8px', paddingLeft: `${6 + (depth + 1) * 14 + 12}px`, cursor: 'pointer', fontSize: '13px', borderRadius: '3px', background: selectedName === c.name ? '#33291a' : 'transparent', color: selectedName === c.name ? '#f4902c' : '#ddd' }}>
                            🎵 {c.name}
                        </div>
                    )
            ))}
        </div>
    );
};

window.SoundBrowse = ({ onClose, onChoose, targetLabel }) => {
    const supportsFS = typeof window.showDirectoryPicker === 'function';
    const [rootHandle, setRootHandle] = React.useState(supportsFS ? (window.OA_SOUND_DIR || null) : null);
    const [flatEntries, setFlatEntries] = React.useState([]); // fallback list
    const [selected, setSelected] = React.useState(null);     // {name, file, url}
    const [buffer, setBuffer] = React.useState(null);
    const [playing, setPlaying] = React.useState(false);
    const [loop, setLoop] = React.useState(false);
    const [autoPreview, setAutoPreview] = React.useState(true);
    const [pos, setPos] = React.useState(0);
    const [busy, setBusy] = React.useState(false);
    const [err, setErr] = React.useState('');

    const audioRef = React.useRef(null);
    const canvasRef = React.useRef(null);

    const pickFolder = async () => {
        try { const h = await window.showDirectoryPicker(); window.OA_SOUND_DIR = h; setRootHandle(h); }
        catch (e) { /* cancelled */ }
    };
    const onPlainFiles = (fileList) => {
        setFlatEntries(sortEntries(Array.from(fileList || []).filter((f) => AUDIO_RE.test(f.name)).map((f) => ({ name: f.name, kind: 'file', file: f }))));
    };

    // Select + preload (decode for waveform, prep object URL for the audio element).
    const selectEntry = async (entry, folder) => {
        setBusy(true); setErr('');
        try {
            const file = entry.file || await entry.handle.getFile();
            const url = URL.createObjectURL(file);
            if (selected && selected.url) URL.revokeObjectURL(selected.url);
            setSelected({ name: entry.name, file, url, folder: folder || '' });
            setPos(0);
            try { const ctx = window.oaAudioCtx(); setBuffer(await ctx.decodeAudioData(await file.arrayBuffer())); }
            catch (e) { setBuffer(null); }
        } catch (e) { setErr('Could not open file.'); }
        setBusy(false);
    };
    React.useEffect(() => () => { if (selected && selected.url) URL.revokeObjectURL(selected.url); }, [selected]);

    // Auto-preview the first 5 seconds when a file is selected.
    React.useEffect(() => {
        if (!selected || !autoPreview) return;
        const a = audioRef.current; if (!a) return;
        let stopTimer = null;
        const start = () => {
            a.currentTime = 0;
            const p = a.play(); if (p && p.catch) p.catch(() => {});
            setPlaying(true);
            stopTimer = setTimeout(() => { a.pause(); setPlaying(false); }, 5000);
        };
        // Wait until the new src is loadable, then play.
        if (a.readyState >= 2) start(); else a.addEventListener('canplay', start, { once: true });
        return () => { if (stopTimer) clearTimeout(stopTimer); a.removeEventListener('canplay', start); };
    }, [selected, autoPreview]);

    // Waveform
    React.useEffect(() => {
        const c = canvasRef.current; if (!c) return;
        c.width = c.clientWidth; c.height = c.clientHeight;
        const cx = c.getContext('2d');
        cx.fillStyle = '#0a0a0a'; cx.fillRect(0, 0, c.width, c.height);
        if (!buffer) return;
        const data = buffer.getChannelData(0);
        const step = Math.ceil(data.length / c.width); const amp = c.height / 2;
        cx.strokeStyle = '#f4902c'; cx.beginPath();
        for (let x = 0; x < c.width; x++) { let mn = 1, mx = -1; for (let j = 0; j < step; j++) { const d = data[x * step + j]; if (d === undefined) break; if (d < mn) mn = d; if (d > mx) mx = d; } cx.moveTo(x, (1 + mn) * amp); cx.lineTo(x, (1 + mx) * amp); }
        cx.stroke();
    }, [buffer]);

    const togglePlay = () => {
        const a = audioRef.current; if (!a) return;
        if (playing) { a.pause(); setPlaying(false); }
        else { a.play().then(() => setPlaying(true)).catch(() => {}); }
    };
    const rewind = () => { const a = audioRef.current; if (a) { a.currentTime = 0; setPos(0); } };
    const scrub = (e) => {
        const a = audioRef.current; if (!a || !a.duration) return;
        const rect = e.currentTarget.getBoundingClientRect();
        const frac = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
        a.currentTime = frac * a.duration; setPos(frac);
    };
    React.useEffect(() => { if (audioRef.current) audioRef.current.loop = loop; }, [loop]);
    const chooseIt = () => { if (selected && onChoose) onChoose(selected.file, { name: selected.name, folder: selected.folder || '' }); };

    const tbtn = (extra) => ({ background: '#333', color: '#fff', border: '1px solid #444', borderRadius: '3px', padding: '6px 12px', cursor: 'pointer', fontSize: '13px', ...extra });

    return (
        <div onClick={onClose} style={{ position: 'fixed', inset: 0, zIndex: 10000, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'sans-serif' }}>
            <div onClick={(e) => e.stopPropagation()} style={{ width: '620px', maxWidth: '94vw', maxHeight: '88vh', display: 'flex', flexDirection: 'column', background: '#1c1c1c', border: '1px solid #f4902c', borderRadius: '6px', color: '#eee', boxShadow: '0 10px 40px rgba(0,0,0,0.6)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid #333' }}>
                    <h3 style={{ margin: 0, color: '#f4902c', textTransform: 'uppercase', letterSpacing: '1px', fontSize: '15px' }}>
                        Sound Browse{targetLabel ? ` → ${targetLabel}` : ''}
                    </h3>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#888', fontSize: '20px', cursor: 'pointer' }}>×</button>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 16px', borderBottom: '1px solid #2a2a2a', flexWrap: 'wrap' }}>
                    {supportsFS ? (
                        <button onClick={pickFolder} style={tbtn({ background: '#f4902c', color: '#111', border: 'none', fontWeight: 'bold' })}>📁 Choose folder…</button>
                    ) : (
                        <label style={tbtn({ background: '#f4902c', color: '#111', border: 'none', fontWeight: 'bold' })}>
                            📁 Choose files…
                            <input type="file" accept="audio/*" multiple style={{ display: 'none' }} onChange={(e) => onPlainFiles(e.target.files)} />
                        </label>
                    )}
                    <label style={{ fontSize: '12px', color: '#ccc', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <input type="checkbox" checked={autoPreview} onChange={(e) => setAutoPreview(e.target.checked)} /> Auto-preview 5s
                    </label>
                </div>

                {err && <div style={{ padding: '6px 16px', color: '#f88', fontSize: '12px' }}>⚠️ {err}</div>}

                {/* Folder tree (or flat fallback list) */}
                <div style={{ flex: 1, minHeight: '150px', maxHeight: '34vh', overflowY: 'auto', padding: '6px 4px' }}>
                    {rootHandle ? (
                        <SoundTreeNode name={rootHandle.name || 'root'} handle={rootHandle} depth={0} defaultOpen onSelectFile={selectEntry} selectedName={selected && selected.name} pathPrefix={rootHandle.name || 'root'} />
                    ) : flatEntries.length > 0 ? (
                        flatEntries.map((entry, i) => (
                            <div key={i} onClick={() => selectEntry(entry, '')} style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '4px 8px', borderRadius: '3px', cursor: 'pointer', background: selected && selected.name === entry.name ? '#33291a' : 'transparent', fontSize: '13px', color: selected && selected.name === entry.name ? '#f4902c' : '#ddd' }}>
                                🎵 {entry.name}
                            </div>
                        ))
                    ) : (
                        <div style={{ color: '#666', fontSize: '12px', padding: '20px', textAlign: 'center' }}>
                            {supportsFS ? 'Choose a folder to browse its tree.' : 'Choose audio files to preview and load.'}
                        </div>
                    )}
                </div>

                {/* Preview + transport */}
                <div style={{ borderTop: '1px solid #333', padding: '10px 16px' }}>
                    <div style={{ fontSize: '12px', color: '#aaa', marginBottom: '6px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {busy ? 'Loading…' : (selected ? selected.name : 'No file selected')}
                    </div>
                    <div onClick={scrub} style={{ position: 'relative', width: '100%', height: '72px', background: '#0a0a0a', border: '1px solid #444', cursor: selected ? 'pointer' : 'default' }}>
                        <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />
                        {selected && <div style={{ position: 'absolute', top: 0, bottom: 0, left: `${pos * 100}%`, width: '2px', background: '#fff', pointerEvents: 'none' }} />}
                    </div>
                    <audio
                        ref={audioRef}
                        src={selected ? selected.url : undefined}
                        onTimeUpdate={(e) => { const a = e.currentTarget; if (a.duration) setPos(a.currentTime / a.duration); }}
                        onEnded={() => { if (!loop) setPlaying(false); }}
                        style={{ display: 'none' }}
                    />
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '10px' }}>
                        <button onClick={rewind} disabled={!selected} style={tbtn()}>⏮ Rewind</button>
                        <button onClick={togglePlay} disabled={!selected} style={tbtn({ background: playing ? '#c00' : '#388e3c', border: 'none', fontWeight: 'bold' })}>{playing ? '⏸ Pause' : '► Play'}</button>
                        <label style={{ fontSize: '12px', color: '#ccc', display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <input type="checkbox" checked={loop} onChange={(e) => setLoop(e.target.checked)} /> Loop
                        </label>
                        <div style={{ flexGrow: 1 }} />
                        <button onClick={chooseIt} disabled={!selected} style={tbtn({ background: selected ? '#f4902c' : '#553', color: '#111', border: 'none', fontWeight: 'bold', padding: '8px 16px', cursor: selected ? 'pointer' : 'not-allowed' })}>
                            ⭳ Load to pad
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
