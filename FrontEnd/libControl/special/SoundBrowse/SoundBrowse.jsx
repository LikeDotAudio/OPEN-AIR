/**
 * SoundBrowse.jsx — custom "Sound Browse" window.
 * Two panes: a folder TREE on the left, and a grid of RENDERED WAVEFORM
 * thumbnails for the selected folder on the right. Click (or arrow-key) a
 * waveform to select + auto-play it; scrub / rewind / loop below; Load to pad.
 *
 * Playback is Web Audio (BufferSource) off the decoded buffer, so every format
 * we can decode — including AIFF via oaDecodeAudio — previews correctly.
 * Folder tree uses the File System Access API (Chromium); elsewhere it falls
 * back to a flat multi-file picker shown in the grid.
 */
const AUDIO_RE = /\.(mp3|wav|wave|aif|aiff|aac|m4a|ogg|oga|flac|opus)$/i;
const COLS = 3;   // grid columns (drives arrow up/down)

const drawWave = (canvas, buffer, color) => {
    if (!canvas) return;
    canvas.width = canvas.clientWidth || 120;
    canvas.height = canvas.clientHeight || 48;
    const cx = canvas.getContext('2d');
    cx.fillStyle = '#0a0a0a'; cx.fillRect(0, 0, canvas.width, canvas.height);
    if (!buffer) return;
    const data = buffer.getChannelData(0);
    const step = Math.max(1, Math.ceil(data.length / canvas.width));
    const amp = canvas.height / 2;
    cx.strokeStyle = color || '#f4902c'; cx.beginPath();
    for (let x = 0; x < canvas.width; x++) {
        let mn = 1, mx = -1;
        for (let j = 0; j < step; j++) { const d = data[x * step + j]; if (d === undefined) break; if (d < mn) mn = d; if (d > mx) mx = d; }
        cx.moveTo(x, (1 + mn) * amp); cx.lineTo(x, (1 + mx) * amp);
    }
    cx.stroke();
};

// A single waveform thumbnail — decodes its file to render the wave, but only
// once it scrolls into view (a recursive folder scan can yield thousands).
const WaveThumb = ({ entry, selected, onSelect, scrollRootRef }) => {
    const canvasRef = React.useRef(null);
    const wrapRef = React.useRef(null);
    const [visible, setVisible] = React.useState(false);
    React.useEffect(() => {
        const el = wrapRef.current;
        if (!el || typeof IntersectionObserver === 'undefined') { setVisible(true); return; }
        const io = new IntersectionObserver((es) => { if (es[0].isIntersecting) { setVisible(true); io.disconnect(); } }, { root: (scrollRootRef && scrollRootRef.current) || null, rootMargin: '200px' });
        io.observe(el);
        return () => io.disconnect();
    }, []);
    React.useEffect(() => {
        if (!visible) return;
        let cancelled = false;
        (async () => {
            try {
                const file = entry.file || await entry.handle.getFile();
                const buf = await window.oaDecodeAudio(window.oaAudioCtx(), await file.arrayBuffer());
                if (!cancelled) drawWave(canvasRef.current, buf, selected ? '#ffb74d' : '#f4902c');
            } catch (e) { /* undecodable — leave blank */ }
        })();
        return () => { cancelled = true; };
    }, [entry, visible]);
    return (
        <div ref={wrapRef} onClick={onSelect} title={entry.sub ? `${entry.sub}/${entry.name}` : entry.name}
            style={{ border: selected ? '2px solid #f4902c' : '1px solid #444', borderRadius: '4px', padding: '4px', cursor: 'pointer', background: selected ? '#2a2018' : '#141414', boxSizing: 'border-box' }}>
            <canvas ref={canvasRef} style={{ width: '100%', height: '46px', display: 'block', background: '#0a0a0a' }} />
            <div style={{ fontSize: '10px', color: selected ? '#f4902c' : '#bbb', marginTop: '3px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{entry.name}</div>
        </div>
    );
};

// Recursively collect audio files (with their sub-path) from a folder tree.
const MAX_FILES = 4000;
const gatherFiles = async (handle, prefix, out, depth) => {
    if (depth > 8 || out.length >= MAX_FILES) return;
    const subdirs = [];
    for await (const [n, h] of handle.entries()) {
        if (out.length >= MAX_FILES) break;
        if (h.kind === 'directory') subdirs.push([n, h]);
        else if (AUDIO_RE.test(n)) out.push({ name: n, handle: h, sub: prefix });
    }
    for (const [n, h] of subdirs) { if (out.length >= MAX_FILES) break; await gatherFiles(h, prefix ? `${prefix}/${n}` : n, out, depth + 1); }
};

// Find recurring name phrases across the gathered files → quick-filter chips.
// Ranks tokens by how many distinct sub-folders they appear in, then frequency.
const computeChips = (files) => {
    const map = new Map(); // lowerToken -> { display, count, folders:Set }
    files.forEach((f) => {
        const base = f.name.replace(/\.[^.]+$/, '');
        const parts = base.split(/[^A-Za-z0-9]+/).filter((t) => t.length >= 2 && !/^\d+$/.test(t));
        const seen = new Set();
        parts.forEach((p) => {
            const k = p.toLowerCase();
            if (seen.has(k)) return; seen.add(k);
            let e = map.get(k); if (!e) { e = { display: p, count: 0, folders: new Set() }; map.set(k, e); }
            e.count++; e.folders.add(f.sub || '');
        });
    });
    return Array.from(map.values())
        .filter((e) => e.count >= 2)
        .sort((a, b) => (b.folders.size - a.folders.size) || (b.count - a.count))
        .slice(0, 14);
};

// Folders-only tree node (files live in the right-hand grid).
const SoundFolderNode = ({ name, handle, depth, defaultOpen, onSelectFolder, selectedFolder, pathPrefix }) => {
    const [open, setOpen] = React.useState(!!defaultOpen);
    const [subdirs, setSubdirs] = React.useState(null);
    const load = async () => {
        const dirs = [];
        try { for await (const [n, h] of handle.entries()) if (h.kind === 'directory') dirs.push({ name: n, handle: h }); } catch (e) {}
        dirs.sort((a, b) => a.name.localeCompare(b.name));
        setSubdirs(dirs);
    };
    React.useEffect(() => { if (defaultOpen && subdirs === null) load(); }, []);
    const isSel = selectedFolder === handle;
    return (
        <div>
            <div onClick={() => { onSelectFolder(handle, pathPrefix); if (!open) { setOpen(true); if (subdirs === null) load(); } }}
                style={{ display: 'flex', alignItems: 'center', gap: '3px', padding: '3px 4px', paddingLeft: `${4 + depth * 12}px`, cursor: 'pointer', fontSize: '12px', background: isSel ? '#33291a' : 'transparent', color: isSel ? '#f4902c' : '#cdd', borderRadius: '3px' }}>
                <span onClick={(e) => { e.stopPropagation(); const nx = !open; setOpen(nx); if (nx && subdirs === null) load(); }} style={{ width: '10px', color: '#888' }}>{open ? '▾' : '▸'}</span>
                <span>📁 {name}</span>
            </div>
            {open && subdirs && subdirs.map((d, i) => (
                <SoundFolderNode key={i} name={d.name} handle={d.handle} depth={depth + 1} onSelectFolder={onSelectFolder} selectedFolder={selectedFolder} pathPrefix={`${pathPrefix}/${d.name}`} />
            ))}
        </div>
    );
};

window.SoundBrowse = ({ onClose, onChoose, onChooseOther, targetLabel }) => {
    const supportsFS = typeof window.showDirectoryPicker === 'function';
    const [rootHandle, setRootHandle] = React.useState(supportsFS ? (window.OA_SOUND_DIR || null) : null);
    const [selectedFolder, setSelectedFolder] = React.useState(null);
    const [selectedFolderPath, setSelectedFolderPath] = React.useState('');
    const [folderFiles, setFolderFiles] = React.useState([]);
    const [flatEntries, setFlatEntries] = React.useState([]);
    const [selectedIndex, setSelectedIndex] = React.useState(-1);
    const [selected, setSelected] = React.useState(null);   // {name, file, folder}
    const [buffer, setBuffer] = React.useState(null);
    const [playing, setPlaying] = React.useState(false);
    const [loop, setLoop] = React.useState(false);
    const [autoPreview, setAutoPreview] = React.useState(true);
    const [pos, setPos] = React.useState(0);
    const [err, setErr] = React.useState('');
    const [chips, setChips] = React.useState([]);
    const [scanning, setScanning] = React.useState(false);

    const bigCanvasRef = React.useRef(null);
    const gridScrollRef = React.useRef(null);
    const selectedThumbRef = React.useRef(null);
    const srcRef = React.useRef(null);
    const startTimeRef = React.useRef(0);
    const offsetRef = React.useRef(0);
    const rafRef = React.useRef(null);

    const [filter, setFilter] = React.useState('');
    const files = supportsFS ? folderFiles : flatEntries;
    const shown = filter.trim() ? files.filter((f) => f.name.toLowerCase().includes(filter.trim().toLowerCase())) : files;
    const duration = buffer ? buffer.duration : 0;

    const pickFolder = async () => {
        try {
            const h = await window.showDirectoryPicker();
            window.OA_SOUND_DIR = h; setRootHandle(h);
            if (window.oaIdbSet) window.oaIdbSet('oaRootDir', h).catch(() => {}); // persist for revert
            selectFolder(h, h.name || 'root');
        } catch (e) { /* cancelled */ }
    };
    const selectFolder = async (handle, path) => {
        setSelectedFolder(handle); setSelectedFolderPath(path || ''); setSelectedIndex(-1); setErr(''); setFilter(''); setScanning(true); setChips([]);
        const items = [];
        // Recurse through every sub-folder so all files show flattened in the grid.
        try { await gatherFiles(handle, '', items, 0); }
        catch (e) { setErr('Could not read folder.'); }
        items.sort((a, b) => (a.sub === b.sub ? a.name.localeCompare(b.name) : (a.sub || '').localeCompare(b.sub || '')));
        setFolderFiles(items);
        setChips(computeChips(items));
        setScanning(false);
        if (items.length >= MAX_FILES) setErr(`Showing the first ${MAX_FILES} files.`);
    };
    const onPlainFiles = (fileList) => {
        setFlatEntries(Array.from(fileList || []).filter((f) => AUDIO_RE.test(f.name)).map((f) => ({ name: f.name, file: f })));
        setSelectedIndex(-1);
    };

    const selectFileByIndex = async (idx) => {
        if (idx < 0 || idx >= shown.length) return;
        setSelectedIndex(idx);
        const entry = shown[idx];
        try {
            const file = entry.file || await entry.handle.getFile();
            const folder = supportsFS ? (selectedFolderPath + (entry.sub ? '/' + entry.sub : '')) : '';
            setSelected({ name: entry.name, file, folder });
            setPos(0);
            try { setBuffer(await window.oaDecodeAudio(window.oaAudioCtx(), await file.arrayBuffer())); } catch (e) { setBuffer(null); }
        } catch (e) { setErr('Could not open file.'); }
    };

    // ---- Web Audio transport (works for every decodable format incl. AIFF) ---
    const stopSrc = () => { if (srcRef.current) { try { srcRef.current.stop(); } catch (e) {} srcRef.current = null; } if (rafRef.current) cancelAnimationFrame(rafRef.current); };
    const playFrom = (frac) => {
        if (!buffer) return;
        stopSrc();
        const ctx = window.oaAudioCtx();
        const src = ctx.createBufferSource();
        src.buffer = buffer; src.loop = loop; src.connect(ctx.destination);
        const startOffset = Math.max(0, Math.min(0.999, frac)) * buffer.duration;
        src.start(0, startOffset);
        srcRef.current = src; startTimeRef.current = ctx.currentTime; offsetRef.current = startOffset;
        src.onended = () => { if (srcRef.current === src) { srcRef.current = null; if (!loop) setPlaying(false); } };
        setPlaying(true);
        const update = () => {
            if (!srcRef.current) return;
            let t = offsetRef.current + (ctx.currentTime - startTimeRef.current);
            if (loop && buffer.duration) t = t % buffer.duration;
            setPos(buffer.duration ? Math.min(1, t / buffer.duration) : 0);
            rafRef.current = requestAnimationFrame(update);
        };
        rafRef.current = requestAnimationFrame(update);
    };
    const togglePlay = () => { if (playing) { stopSrc(); setPlaying(false); } else { playFrom(pos); } };
    const rewind = () => { setPos(0); if (playing) playFrom(0); };
    const scrub = (e) => { if (!duration) return; const rect = e.currentTarget.getBoundingClientRect(); const frac = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width)); setPos(frac); if (playing) playFrom(frac); };
    React.useEffect(() => { if (srcRef.current) srcRef.current.loop = loop; }, [loop]);
    React.useEffect(() => () => stopSrc(), []);

    // Auto-preview the first 5 seconds when a new buffer is ready.
    React.useEffect(() => {
        if (!buffer || !autoPreview) return;
        playFrom(0);
        const stop = setTimeout(() => { stopSrc(); setPlaying(false); }, 5000);
        return () => clearTimeout(stop);
    }, [buffer, autoPreview]);

    // Big waveform of the selected file.
    React.useEffect(() => { drawWave(bigCanvasRef.current, buffer, '#f4902c'); }, [buffer]);

    // Keep the selected thumbnail centered in the grid as you browse.
    React.useEffect(() => {
        const el = selectedThumbRef.current, cont = gridScrollRef.current;
        if (!el || !cont) return;
        const cr = cont.getBoundingClientRect(), er = el.getBoundingClientRect();
        const delta = (er.top - cr.top) - (cont.clientHeight / 2 - el.clientHeight / 2);
        if (Math.abs(delta) > 2) cont.scrollTo({ top: cont.scrollTop + delta, behavior: 'smooth' });
    }, [selectedIndex]);

    // Arrow-key navigation across the thumbnail grid; Enter = Load.
    React.useEffect(() => {
        const onKey = (e) => {
            if (e.target && (e.target.tagName === 'INPUT')) return;  // don't hijack the filter box
            if (!shown.length) return;
            let d = 0;
            // Snake traversal: forward advances one (…over, over, over, down a row),
            // back reverses, both wrapping around the whole grid.
            if (e.key === 'ArrowRight' || e.key === 'ArrowDown') d = 1;
            else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') d = -1;
            else if (e.key === 'Enter') { chooseIt(); e.preventDefault(); return; }
            else return;
            e.preventDefault();
            const n = shown.length;
            const base = selectedIndex < 0 ? (d > 0 ? -1 : 0) : selectedIndex;
            selectFileByIndex(((base + d) % n + n) % n);
        };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, [shown, selectedIndex, selectedFolderPath, selected]);

    const chooseIt = () => { if (selected && onChoose) onChoose(selected.file, { name: selected.name, folder: selected.folder || '' }); };
    const chooseOther = () => { if (selected && onChooseOther) onChooseOther(selected.file, { name: selected.name, folder: selected.folder || '' }); };

    const tbtn = (extra) => ({ background: '#333', color: '#fff', border: '1px solid #444', borderRadius: '3px', padding: '6px 12px', cursor: 'pointer', fontSize: '13px', ...extra });

    return (
        <div onClick={onClose} style={{ position: 'fixed', inset: 0, zIndex: 10000, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'sans-serif' }}>
            <div onClick={(e) => e.stopPropagation()} style={{ width: '760px', maxWidth: '95vw', height: '80vh', display: 'flex', flexDirection: 'column', background: '#1c1c1c', border: '1px solid #f4902c', borderRadius: '6px', color: '#eee', boxShadow: '0 10px 40px rgba(0,0,0,0.6)' }}>
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
                    <input type="text" value={filter} onChange={(e) => { setFilter(e.target.value); setSelectedIndex(-1); }} placeholder="Filter (e.g. HH)"
                        style={{ background: '#111', color: '#eee', border: '1px solid #444', borderRadius: '3px', padding: '4px 8px', fontSize: '12px', width: '130px' }} />
                    <span style={{ fontSize: '11px', color: '#666' }}>↑ ↓ ← → browse · Enter load</span>
                </div>

                {err && <div style={{ padding: '6px 16px', color: '#f88', fontSize: '12px' }}>⚠️ {err}</div>}

                <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
                    <div style={{ width: '210px', flexShrink: 0, borderRight: '1px solid #333', overflowY: 'auto', padding: '6px 4px' }}>
                        {rootHandle ? (
                            <SoundFolderNode name={rootHandle.name || 'root'} handle={rootHandle} depth={0} defaultOpen onSelectFolder={selectFolder} selectedFolder={selectedFolder} pathPrefix={rootHandle.name || 'root'} />
                        ) : (
                            <div style={{ color: '#666', fontSize: '11px', padding: '12px' }}>
                                {supportsFS ? 'Choose a folder to see its tree.' : 'Choose files to browse.'}
                            </div>
                        )}
                    </div>
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
                        {(chips.length > 0 || scanning) && (
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', padding: '6px 10px', borderBottom: '1px solid #2a2a2a', alignItems: 'center' }}>
                                {scanning && <span style={{ fontSize: '11px', color: '#888' }}>scanning…</span>}
                                {chips.map((c, i) => {
                                    const active = filter.toLowerCase() === c.display.toLowerCase();
                                    return (
                                        <button key={i} onClick={() => { setFilter(active ? '' : c.display); setSelectedIndex(-1); }}
                                            title={`${c.count} files · ${c.folders.size} folders`}
                                            style={{ background: active ? '#f4902c' : '#2a2a2a', color: active ? '#111' : '#cde', border: '1px solid #444', borderRadius: '12px', padding: '2px 9px', fontSize: '11px', cursor: 'pointer' }}>
                                            {c.display}
                                        </button>
                                    );
                                })}
                                {filter && <button onClick={() => setFilter('')} style={{ background: 'none', border: 'none', color: '#888', fontSize: '11px', cursor: 'pointer' }}>clear</button>}
                            </div>
                        )}
                        <div ref={gridScrollRef} style={{ flex: 1, overflowY: 'auto', padding: '10px' }}>
                            {shown.length > 0 ? (
                                <div style={{ display: 'grid', gridTemplateColumns: `repeat(${COLS}, 1fr)`, gap: '8px' }}>
                                    {shown.map((entry, i) => (
                                        <div key={i} ref={i === selectedIndex ? selectedThumbRef : undefined}>
                                            <WaveThumb entry={entry} selected={i === selectedIndex} onSelect={() => selectFileByIndex(i)} scrollRootRef={gridScrollRef} />
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div style={{ color: '#666', fontSize: '12px', padding: '30px', textAlign: 'center' }}>
                                    {scanning ? 'Scanning folders…' : (files.length ? 'No files match the filter.' : (supportsFS ? 'Select a folder on the left to see its waveforms.' : 'No files chosen yet.'))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                <div style={{ borderTop: '1px solid #333', padding: '10px 16px' }}>
                    <div style={{ fontSize: '12px', color: '#aaa', marginBottom: '6px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {selected ? selected.name : 'No file selected'}
                    </div>
                    <div onClick={scrub} style={{ position: 'relative', width: '100%', height: '60px', background: '#0a0a0a', border: '1px solid #444', cursor: selected ? 'pointer' : 'default' }}>
                        <canvas ref={bigCanvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />
                        {selected && <div style={{ position: 'absolute', top: 0, bottom: 0, left: `${pos * 100}%`, width: '2px', background: '#fff', pointerEvents: 'none' }} />}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '10px' }}>
                        <button onClick={rewind} disabled={!selected} style={tbtn()}>⏮ Rewind</button>
                        <button onClick={togglePlay} disabled={!selected} style={tbtn({ background: playing ? '#c00' : '#388e3c', border: 'none', fontWeight: 'bold' })}>{playing ? '⏸ Pause' : '► Play'}</button>
                        <label style={{ fontSize: '12px', color: '#ccc', display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <input type="checkbox" checked={loop} onChange={(e) => setLoop(e.target.checked)} /> Loop
                        </label>
                        <div style={{ flexGrow: 1 }} />
                        <button onClick={chooseIt} disabled={!selected} style={tbtn({ background: selected ? '#f4902c' : '#553', color: '#111', border: 'none', fontWeight: 'bold', padding: '8px 14px', cursor: selected ? 'pointer' : 'not-allowed' })}>
                            ⭳ Load to {targetLabel || 'pad'}
                        </button>
                        {onChooseOther && (
                            <button onClick={chooseOther} disabled={!selected} style={tbtn({ background: selected ? '#8ab4f8' : '#345', color: '#111', border: 'none', fontWeight: 'bold', padding: '8px 14px', cursor: selected ? 'pointer' : 'not-allowed' })}>
                                ⭳ Load to other pad
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};
