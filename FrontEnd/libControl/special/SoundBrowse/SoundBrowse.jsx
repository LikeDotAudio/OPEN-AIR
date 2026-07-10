/**
 * SoundBrowse.jsx — custom "Sound Browse" window (replaces the native file
 * dialog for loading pad samples). Navigate a folder, preview with a waveform,
 * scrub / play / rewind / loop, then Load onto the target pad.
 *
 * Directory navigation uses the File System Access API (showDirectoryPicker,
 * Chromium). Where that's unavailable it falls back to a multi-file picker.
 */
const AUDIO_RE = /\.(mp3|wav|wave|aif|aiff|aac|m4a|ogg|oga|flac|opus)$/i;

window.SoundBrowse = ({ onClose, onChoose, targetLabel }) => {
    const supportsFS = typeof window.showDirectoryPicker === 'function';
    const [entries, setEntries] = React.useState([]);      // {name, kind, handle?/file?}
    const [pathStack, setPathStack] = React.useState([]);  // [{name, handle}] breadcrumb
    const [selected, setSelected] = React.useState(null);  // {name, file, url}
    const [buffer, setBuffer] = React.useState(null);      // decoded (for waveform)
    const [playing, setPlaying] = React.useState(false);
    const [loop, setLoop] = React.useState(false);
    const [pos, setPos] = React.useState(0);               // 0..1
    const [busy, setBusy] = React.useState(false);
    const [err, setErr] = React.useState('');

    const audioRef = React.useRef(null);
    const canvasRef = React.useRef(null);

    // ---- Directory listing ---------------------------------------------------
    const listDir = async (handle) => {
        setErr('');
        const items = [];
        try {
            for await (const [name, h] of handle.entries()) {
                if (h.kind === 'directory') items.push({ name, kind: 'dir', handle: h });
                else if (AUDIO_RE.test(name)) items.push({ name, kind: 'file', handle: h });
            }
        } catch (e) { setErr('Could not read folder.'); }
        items.sort((a, b) => (a.kind === b.kind ? a.name.localeCompare(b.name) : (a.kind === 'dir' ? -1 : 1)));
        setEntries(items);
    };

    const pickFolder = async () => {
        try {
            const h = await window.showDirectoryPicker();
            window.OA_SOUND_DIR = h;
            setPathStack([{ name: h.name || 'root', handle: h }]);
            listDir(h);
        } catch (e) { /* user cancelled */ }
    };

    // Reopen the last-used folder on mount if we have one.
    React.useEffect(() => {
        if (supportsFS && window.OA_SOUND_DIR) {
            setPathStack([{ name: window.OA_SOUND_DIR.name || 'root', handle: window.OA_SOUND_DIR }]);
            listDir(window.OA_SOUND_DIR);
        }
    }, []);

    const enterDir = (entry) => { setPathStack((p) => [...p, { name: entry.name, handle: entry.handle }]); listDir(entry.handle); };
    const goCrumb = (i) => { const h = pathStack[i].handle; setPathStack(pathStack.slice(0, i + 1)); listDir(h); };

    // Fallback: plain multi-file picker -> synthesize a flat "folder".
    const onPlainFiles = (fileList) => {
        const arr = Array.from(fileList || []).filter((f) => AUDIO_RE.test(f.name)).map((f) => ({ name: f.name, kind: 'file', file: f }));
        setPathStack([{ name: 'Selected files', handle: null }]);
        setEntries(arr);
    };

    // ---- Select + preload ----------------------------------------------------
    const selectEntry = async (entry) => {
        setBusy(true); setErr('');
        try {
            const file = entry.file || await entry.handle.getFile();
            const url = URL.createObjectURL(file);
            if (selected && selected.url) URL.revokeObjectURL(selected.url);
            setSelected({ name: entry.name, file, url });
            setPos(0); setPlaying(false);
            // Preload/decode for the waveform (best-effort).
            try {
                const ctx = window.oaAudioCtx();
                setBuffer(await ctx.decodeAudioData(await file.arrayBuffer()));
            } catch (e) { setBuffer(null); }
        } catch (e) { setErr('Could not open file.'); }
        setBusy(false);
    };

    React.useEffect(() => () => { if (selected && selected.url) URL.revokeObjectURL(selected.url); }, [selected]);

    // ---- Waveform draw -------------------------------------------------------
    React.useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        canvas.width = canvas.clientWidth; canvas.height = canvas.clientHeight;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#0a0a0a'; ctx.fillRect(0, 0, canvas.width, canvas.height);
        if (!buffer) return;
        const data = buffer.getChannelData(0);
        const step = Math.ceil(data.length / canvas.width);
        const amp = canvas.height / 2;
        ctx.strokeStyle = '#f4902c'; ctx.beginPath();
        for (let x = 0; x < canvas.width; x++) {
            let min = 1, max = -1;
            for (let j = 0; j < step; j++) { const d = data[x * step + j]; if (d === undefined) break; if (d < min) min = d; if (d > max) max = d; }
            ctx.moveTo(x, (1 + min) * amp); ctx.lineTo(x, (1 + max) * amp);
        }
        ctx.stroke();
    }, [buffer]);

    // ---- Transport -----------------------------------------------------------
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

    const chooseIt = () => { if (selected && onChoose) onChoose(selected.file); };

    const tbtn = (extra) => ({ background: '#333', color: '#fff', border: '1px solid #444', borderRadius: '3px', padding: '6px 12px', cursor: 'pointer', fontSize: '13px', ...extra });

    return (
        <div onClick={onClose} style={{ position: 'fixed', inset: 0, zIndex: 10000, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'sans-serif' }}>
            <div onClick={(e) => e.stopPropagation()} style={{ width: '620px', maxWidth: '94vw', maxHeight: '88vh', display: 'flex', flexDirection: 'column', background: '#1c1c1c', border: '1px solid #f4902c', borderRadius: '6px', color: '#eee', boxShadow: '0 10px 40px rgba(0,0,0,0.6)' }}>
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid #333' }}>
                    <h3 style={{ margin: 0, color: '#f4902c', textTransform: 'uppercase', letterSpacing: '1px', fontSize: '15px' }}>
                        Sound Browse{targetLabel ? ` → ${targetLabel}` : ''}
                    </h3>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#888', fontSize: '20px', cursor: 'pointer' }}>×</button>
                </div>

                {/* Toolbar: choose folder / files + breadcrumb */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 16px', borderBottom: '1px solid #2a2a2a', flexWrap: 'wrap' }}>
                    {supportsFS ? (
                        <button onClick={pickFolder} style={tbtn({ background: '#f4902c', color: '#111', border: 'none', fontWeight: 'bold' })}>📁 Choose folder…</button>
                    ) : (
                        <label style={{ ...tbtn({ background: '#f4902c', color: '#111', border: 'none', fontWeight: 'bold' }) }}>
                            📁 Choose files…
                            <input type="file" accept={'audio/*'} multiple style={{ display: 'none' }} onChange={(e) => onPlainFiles(e.target.files)} />
                        </label>
                    )}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '3px', fontSize: '11px', color: '#aaa', flexWrap: 'wrap' }}>
                        {pathStack.map((c, i) => (
                            <span key={i}>
                                {i > 0 && <span style={{ color: '#555' }}> / </span>}
                                <span onClick={() => c.handle && goCrumb(i)} style={{ cursor: c.handle ? 'pointer' : 'default', color: i === pathStack.length - 1 ? '#f4902c' : '#8ab4f8' }}>{c.name}</span>
                            </span>
                        ))}
                    </div>
                </div>

                {err && <div style={{ padding: '6px 16px', color: '#f88', fontSize: '12px' }}>⚠️ {err}</div>}

                {/* File list */}
                <div style={{ flex: 1, minHeight: '140px', maxHeight: '34vh', overflowY: 'auto', padding: '6px 10px' }}>
                    {entries.length === 0 && (
                        <div style={{ color: '#666', fontSize: '12px', padding: '20px', textAlign: 'center' }}>
                            {supportsFS ? 'Choose a folder to browse audio files.' : 'Choose audio files to preview and load.'}
                        </div>
                    )}
                    {entries.map((entry, i) => {
                        const isSel = selected && selected.name === entry.name && entry.kind === 'file';
                        return (
                            <div key={i}
                                onClick={() => entry.kind === 'dir' ? enterDir(entry) : selectEntry(entry)}
                                style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '4px 8px', borderRadius: '3px', cursor: 'pointer', background: isSel ? '#33291a' : 'transparent', fontSize: '13px' }}>
                                <span>{entry.kind === 'dir' ? '📁' : '🎵'}</span>
                                <span style={{ color: entry.kind === 'dir' ? '#8ab4f8' : (isSel ? '#f4902c' : '#ddd') }}>{entry.name}</span>
                            </div>
                        );
                    })}
                </div>

                {/* Preview + transport */}
                <div style={{ borderTop: '1px solid #333', padding: '10px 16px' }}>
                    <div style={{ fontSize: '12px', color: '#aaa', marginBottom: '6px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {busy ? 'Loading…' : (selected ? selected.name : 'No file selected')}
                    </div>
                    <div onClick={scrub} style={{ position: 'relative', width: '100%', height: '72px', background: '#0a0a0a', border: '1px solid #444', cursor: selected ? 'pointer' : 'default' }}>
                        <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />
                        {selected && (
                            <div style={{ position: 'absolute', top: 0, bottom: 0, left: `${pos * 100}%`, width: '2px', background: '#fff', pointerEvents: 'none' }} />
                        )}
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
