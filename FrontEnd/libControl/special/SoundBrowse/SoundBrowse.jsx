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
const COLS = 4;   // grid columns (drives arrow up/down)

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

const CLOUD_PALETTE = ['#f4902c', '#8ab4f8', '#4caf50', '#e57373', '#ba68c8', '#4dd0e1', '#ffd54f', '#a1887f', '#90a4ae', '#f06292', '#aed581', '#7986cb', '#ff8a65', '#4db6ac', '#dce775', '#9575cd', '#fff'];

const SoundCloudView = ({ data, rootHandle, onSelectFile }) => {
    const chartRef = React.useRef(null);
    const echartsInst = React.useRef(null);
    const [detail, setDetail] = React.useState(null);   // clicked sample → side panel
    // Two separate graphs: one-shots (≤1 transient) vs loops (>1 transient).
    const [mode, setMode] = React.useState('hits');
    // How to colour/group points: auto, blind K-Means cluster, feature timbre, or name.
    const [colorBy, setColorBy] = React.useState('auto');

    const isLoop = (d) => (d.transients || 0) > 1;
    const hits = React.useMemo(() => data.filter((d) => !isLoop(d)), [data]);
    const loops = React.useMemo(() => data.filter((d) => isLoop(d)), [data]);
    const view = mode === 'loops' ? loops : hits;

    const groupKey = (d) => {
        if (colorBy === 'cluster') return 'Cluster ' + (d.cluster != null ? d.cluster : '?');
        if (colorBy === 'name') return d.group || 'Other';
        if (colorBy === 'timbre') return d.timbre || d.group || 'Other';
        return mode === 'loops' ? (d.group || 'Loop') : (d.timbre || d.group || 'Other');
    };
    const groups = React.useMemo(() => Array.from(new Set(view.map(groupKey))).sort(), [view, mode, colorBy]);
    const colorFor = (g) => CLOUD_PALETTE[Math.max(0, groups.indexOf(g)) % CLOUD_PALETTE.length];

    // Load (decode+play) a sample and show its detail.
    const loadAndDetail = async (d) => {
        setDetail(d);
        try {
            let h = rootHandle;
            if (d.sub) { for (const p of d.sub.split(/[\/\\]/)) { if (p) h = await h.getDirectoryHandle(p); } }
            const fh = await h.getFileHandle(d.name);
            const file = await fh.getFile();
            const folder = rootHandle.name + (d.sub ? '/' + d.sub : '');
            onSelectFile({ name: d.name, folder, file });
        } catch (e) { console.error('Could not load file from cloud:', e); }
    };

    React.useEffect(() => {
        if (!chartRef.current || !window.echarts) return;
        const chart = window.echarts.init(chartRef.current, 'dark');
        echartsInst.current = chart;

        const lengths = view.map((d) => d.length || 0.1);
        const minL = Math.min(...lengths, 0.1), maxL = Math.max(...lengths, 5);
        const sz = (l) => 6 + ((l - minL) / (maxL - minL || 1)) * 18;
        // Loops: X = BPM (fallback pitch), Z = length. One-shots: X = pitch, Z = complexity.
        const xOf = (d) => (mode === 'loops' ? (d.bpm || d.pitch || 0) : (d.pitch || 0));
        const zOf = (d) => (mode === 'loops' ? (d.length || 0) : (d.complexity || 0));
        const xName = mode === 'loops' ? 'BPM' : 'Pitch';
        const zName = mode === 'loops' ? 'Length (s)' : 'Complexity';
        const tip = (p) => {
            const d = p.data.raw; const t = d.transients || 0;
            return `<b>${d.name}</b><br/>${groupKey(d)}${t > 1 ? ' · loop' : ''}<br/>`
                + `Pitch ${(d.pitch || 0).toFixed(0)}Hz · Bright ${((d.brightness ?? d.high) || 0).toFixed(2)} · Harm ${(d.harmonicity || 0).toFixed(2)}<br/>`
                + `${(d.length || 0).toFixed(2)}s · ${t} transient${t === 1 ? '' : 's'}${d.bpm ? ' · ' + d.bpm.toFixed(0) + ' BPM' : ''}`;
        };

        // 3D: X, Y (depth) = group, Z (height).
        chart.setOption({
            backgroundColor: 'transparent',
            legend: { type: 'scroll', top: 4, textStyle: { color: '#ccc', fontSize: 10 }, inactiveColor: '#555' },
            tooltip: { formatter: tip },
            xAxis3D: { name: xName, type: 'value', nameTextStyle: { color: '#888' }, axisLabel: { color: '#666' } },
            yAxis3D: { name: 'Group', type: 'category', data: groups, nameTextStyle: { color: '#888' }, axisLabel: { color: '#aaa', fontSize: 9 } },
            zAxis3D: { name: zName, type: 'value', nameTextStyle: { color: '#888' }, axisLabel: { color: '#666' } },
            grid3D: { boxWidth: 100, boxDepth: 90, viewControl: { distance: 220 }, axisLine: { lineStyle: { color: '#444' } }, splitLine: { lineStyle: { color: '#222' } } },
            series: groups.map((g) => ({
                name: g, type: 'scatter3D',
                itemStyle: { color: colorFor(g), opacity: 0.85 },
                emphasis: { itemStyle: { color: '#fff' } },
                data: view.filter((d) => groupKey(d) === g).map((d) => ({ value: [xOf(d), groups.indexOf(g), zOf(d)], raw: d, symbolSize: sz(d.length || 0.1) })),
            })),
        });

        // If echarts-gl isn't available, grid3D won't exist — fall back to 2D.
        let ok3D = false;
        try { ok3D = !!(chart.getModel().getComponent('grid3D')); } catch (e) { ok3D = false; }
        if (!ok3D) {
            chart.clear();
            chart.setOption({
                backgroundColor: 'transparent',
                legend: { type: 'scroll', top: 4, textStyle: { color: '#ccc', fontSize: 10 }, inactiveColor: '#555' },
                tooltip: { formatter: tip },
                grid: { left: 80, right: 20, top: 42, bottom: 40 },
                xAxis: { type: 'value', name: xName, nameTextStyle: { color: '#888' }, axisLabel: { color: '#666' }, splitLine: { show: false } },
                yAxis: { type: 'category', data: groups, name: 'Group', nameTextStyle: { color: '#888' }, axisLabel: { color: '#aaa', fontSize: 10 }, splitLine: { lineStyle: { color: '#222' } } },
                series: groups.map((g) => ({
                    name: g, type: 'scatter', symbolSize: (v, p) => sz(p.data.raw.length),
                    itemStyle: { color: colorFor(g), opacity: 0.75, borderColor: '#000', borderWidth: 0.3 },
                    emphasis: { itemStyle: { borderColor: '#fff', borderWidth: 2 } },
                    data: view.filter((d) => groupKey(d) === g).map((d) => ({ value: [xOf(d), groups.indexOf(g)], raw: d })),
                })),
            });
        }

        const onClick = (params) => { if (params.data && params.data.raw) loadAndDetail(params.data.raw); };
        chart.on('click', onClick);
        const onResize = () => chart.resize();
        window.addEventListener('resize', onResize);
        return () => { window.removeEventListener('resize', onResize); chart.off('click', onClick); chart.dispose(); };
    }, [data, rootHandle, mode, colorBy]);

    const tab = (m, label, n) => (
        <button onClick={() => setMode(m)} style={{
            background: mode === m ? '#f4902c' : '#2a2a2a', color: mode === m ? '#111' : '#bbb',
            border: '1px solid ' + (mode === m ? '#f4902c' : '#444'), borderRadius: '4px',
            padding: '3px 12px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer',
        }}>{label} <span style={{ opacity: 0.7 }}>({n})</span></button>
    );
    const row = (k, v) => (
        <div style={{ marginBottom: '3px' }}>{k}: <b>{v}</b></div>
    );

    return (
        <div style={{ width: '100%', height: '100%', display: 'flex' }}>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
                <div style={{ padding: '6px 16px', background: '#222', borderBottom: '1px solid #333', fontSize: '11px', color: '#888', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    {tab('hits', '● One-shots', hits.length)}
                    {tab('loops', '◆ Loops', loops.length)}
                    <span style={{ marginLeft: '4px' }}>colour by:</span>
                    <select value={colorBy} onChange={(e) => setColorBy(e.target.value)} style={{ background: '#2a2a2a', color: '#ddd', border: '1px solid #444', borderRadius: '4px', fontSize: '11px', padding: '2px 4px' }}>
                        <option value="auto">Auto</option>
                        <option value="cluster">Cluster (K-Means)</option>
                        <option value="timbre">Timbre</option>
                        <option value="name">Name</option>
                    </select>
                    <span style={{ flexGrow: 1 }} />
                    <span>{mode === 'loops'
                        ? 'X: BPM · Y: Group · Z: Length · drag to orbit · click to play'
                        : 'X: Pitch · Y: Group · Z: Complexity · size: Length · click to play'}</span>
                </div>
                <div ref={chartRef} style={{ flex: 1, width: '100%' }} />
            </div>
            <div style={{ width: '196px', flexShrink: 0, borderLeft: '1px solid #333', padding: '12px', overflowY: 'auto', fontSize: '12px', color: '#ccc' }}>
                {detail ? (
                    <div>
                        <div style={{ color: '#f4902c', fontWeight: 'bold', marginBottom: '4px', wordBreak: 'break-word' }}>{detail.name}</div>
                        <div style={{ fontSize: '11px', color: '#8ab4f8', marginBottom: '10px', wordBreak: 'break-word' }}>{detail.sub || '(root)'}</div>
                        <div style={{ marginBottom: '3px' }}>Group: <b style={{ color: colorFor(groupKey(detail)) }}>{detail.group || 'Other'}</b></div>
                        {detail.timbre ? row('Timbre', detail.timbre) : null}
                        {detail.cluster != null && detail.cluster >= 0 ? row('Cluster', '#' + detail.cluster) : null}
                        {row('Pitch', (detail.pitch || 0).toFixed(1) + ' Hz')}
                        {detail.harmonicity != null ? row('Harmonicity', (detail.harmonicity || 0).toFixed(2)) : null}
                        {detail.centroid != null ? row('Brightness', (detail.centroid || 0).toFixed(0) + ' Hz') : null}
                        {row('Complexity', (detail.complexity || 0).toFixed(2))}
                        {detail.attack != null ? row('Attack', (detail.attack || 0).toFixed(3) + ' s') : null}
                        {row('Length', (detail.length || 0).toFixed(2) + ' s')}
                        <div style={{ marginBottom: '3px' }}>Transients: <b>{detail.transients || 0}</b>{(detail.transients || 0) > 1 ? <span style={{ color: '#f4902c', fontWeight: 'bold' }}> — loop</span> : <span style={{ color: '#8a8', fontWeight: 'bold' }}> — one-shot</span>}</div>
                        {detail.bpm ? row('BPM', detail.bpm.toFixed(1)) : null}
                        {detail.sample_rate ? row('Format', (detail.sample_rate / 1000).toFixed(1) + ' kHz / ' + (detail.bit_depth || '?') + '-bit') : null}
                        <button onClick={() => loadAndDetail(detail)} style={{ marginTop: '10px', background: '#388e3c', color: '#fff', border: 'none', borderRadius: '3px', padding: '5px 12px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }}>► Play</button>
                    </div>
                ) : (
                    <div style={{ color: '#666' }}>Click a point to see its details and play it.</div>
                )}
            </div>
        </div>
    );
};

// One pass over the tree: collect ALL filenames (cheap — for the filter chips)
// while capping the file HANDLES kept for the thumbnail grid.
const MAX_FILES = 4000;    // cap on rendered thumbnails
const NAME_MAX = 60000;    // cap on the name-only scan
const gatherAll = async (handle, prefix, files, names, builder, onEmit, depth) => {
    if (depth > 12 || names.length >= NAME_MAX) return;
    const subdirs = [];
    for await (const [n, h] of handle.entries()) {
        if (names.length >= NAME_MAX) break;
        if (h.kind === 'directory') subdirs.push([n, h]);
        else if (AUDIO_RE.test(n)) {
            names.push({ name: n, sub: prefix });
            builder.add(n, prefix);
            if (files.length < MAX_FILES) files.push({ name: n, handle: h, sub: prefix });
            if (names.length % 250 === 0) onEmit();   // grow the chip list live
        }
    }
    for (const [n, h] of subdirs) { if (names.length >= NAME_MAX) break; await gatherAll(h, prefix ? `${prefix}/${n}` : n, files, names, builder, onEmit, depth + 1); }
};

// Deep search: recurse the WHOLE tree (past MAX_FILES) collecting only files whose
// name matches `term` — so a filter finds matches even beyond the initial cap.
const DEEP_MAX = 20000;
const gatherMatching = async (handle, prefix, out, term, depth) => {
    if (depth > 12 || out.length >= DEEP_MAX) return;
    const subdirs = [];
    for await (const [n, h] of handle.entries()) {
        if (out.length >= DEEP_MAX) break;
        if (h.kind === 'directory') subdirs.push([n, h]);
        else if (AUDIO_RE.test(n) && n.toLowerCase().includes(term)) out.push({ name: n, handle: h, sub: prefix });
    }
    for (const [n, h] of subdirs) { if (out.length >= DEEP_MAX) break; await gatherMatching(h, prefix ? `${prefix}/${n}` : n, out, term, depth + 1); }
};

// Incremental builder for the recurring-name chips: add filenames as they're
// discovered and read the current top phrases at any time. Ranks tokens by how
// many distinct sub-folders they appear in, then frequency — so the chip list
// grows live as the tree is scanned.
const makeChipBuilder = () => {
    const map = new Map(); // lowerToken -> { display, count, folders:Set }
    return {
        add(name, sub) {
            const base = name.replace(/\.[^.]+$/, '');
            const parts = base.split(/[^A-Za-z0-9]+/).filter((t) => t.length >= 2 && !/^\d+$/.test(t));
            const seen = new Set();
            parts.forEach((p) => {
                const k = p.toLowerCase();
                if (seen.has(k)) return; seen.add(k);
                let e = map.get(k); if (!e) { e = { display: p, count: 0, folders: new Set() }; map.set(k, e); }
                e.count++; e.folders.add(sub || '');
            });
        },
        top() {
            return Array.from(map.values())
                .filter((e) => e.count >= 2)
                .sort((a, b) => (b.folders.size - a.folders.size) || (b.count - a.count))
                .slice(0, 28);
        },
    };
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

const loadFavs = () => { try { return JSON.parse(window.localStorage.getItem('oaSoundFavs')) || []; } catch (e) { return []; } };

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
    const [deepResults, setDeepResults] = React.useState([]);
    const [deepSearching, setDeepSearching] = React.useState(false);

    // Favorites (liked files), tracked over MQTT (retained) + localStorage.
    const [favState, setFavState] = window.useMqttState('OpenAir/Gui/SoundFavorites', { items: loadFavs() });
    const favorites = (favState && favState.items) || [];
    React.useEffect(() => { try { localStorage.setItem('oaSoundFavs', JSON.stringify(favorites)); } catch (e) {} }, [favState]);
    const [view, setView] = React.useState('files');   // 'files' | 'favorites' | 'cloud'
    const [favEntries, setFavEntries] = React.useState([]);
    const [cloudData, setCloudData] = React.useState(null);
    const [cloudErr, setCloudErr] = React.useState('');
    const isFav = (s) => !!s && favorites.some((f) => f.name === s.name && f.folder === (s.folder || ''));
    const toggleFav = () => {
        if (!selected) return;
        const entry = { name: selected.name, folder: selected.folder || '' };
        const exists = favorites.some((f) => f.name === entry.name && f.folder === entry.folder);
        setFavState({ items: exists ? favorites.filter((f) => !(f.name === entry.name && f.folder === entry.folder)) : [...favorites, entry] });
    };
    const showFiles = () => { setView('files'); setSelectedIndex(-1); };
    const showFavorites = async () => { setView('favorites'); setSelectedIndex(-1); if (window.oaEnsureRootPermission) await window.oaEnsureRootPermission(); };
    const showCloud = async () => { 
        setView('cloud'); setSelectedIndex(-1); setCloudErr('');
        if (!supportsFS || !rootHandle) {
            setCloudErr('Please choose a folder first to view the sample cloud.');
            return;
        }
        try {
            const fh = await rootHandle.getFileHandle('sample_cloud_data.PEAK');
            const file = await fh.getFile();
            const text = await file.text();
            setCloudData(JSON.parse(text));
        } catch (e) {
            setCloudErr('No sample_cloud_data.PEAK found. Run the analyzer on this folder: python3 BackEnd/sample_analyzer_app.py (Rust core, 30 workers).');
            setCloudData(null);
        }
    };
    // Resolve favorite files (from their folder path) when viewing favorites.
    React.useEffect(() => {
        if (view !== 'favorites') return;
        let cancelled = false;
        (async () => {
            const es = await Promise.all(favorites.map(async (f) => {
                const file = window.oaResolveFile ? await window.oaResolveFile(f.folder, f.name) : null;
                return { name: f.name, folder: f.folder, file: file || undefined };
            }));
            if (!cancelled) setFavEntries(es);
        })();
        return () => { cancelled = true; };
    }, [view, favState]);

    const bigCanvasRef = React.useRef(null);
    const gridScrollRef = React.useRef(null);
    const selectedThumbRef = React.useRef(null);
    const srcRef = React.useRef(null);
    const startTimeRef = React.useRef(0);
    const offsetRef = React.useRef(0);
    const rafRef = React.useRef(null);

    const [filter, setFilter] = React.useState('');
    const files = supportsFS ? folderFiles : flatEntries;
    const baseList = view === 'favorites' ? favEntries : files;
    // Filtered view: in the Files view of a real folder we deep-search the whole
    // tree (uncapped); otherwise we just filter the current list.
    const shown = filter.trim()
        ? ((view === 'files' && supportsFS) ? deepResults : baseList.filter((f) => f.name.toLowerCase().includes(filter.trim().toLowerCase())))
        : baseList;
    const duration = buffer ? buffer.duration : 0;

    // Run the uncapped deep search when a filter is set on a real folder.
    React.useEffect(() => {
        const term = filter.trim().toLowerCase();
        if (!term || !supportsFS || !selectedFolder) { setDeepResults([]); setDeepSearching(false); return; }
        let cancelled = false;
        setDeepSearching(true);
        const timer = setTimeout(async () => {
            const out = [];
            try { await gatherMatching(selectedFolder, '', out, term, 0); } catch (e) {}
            if (!cancelled) {
                out.sort((a, b) => (a.sub === b.sub ? a.name.localeCompare(b.name) : (a.sub || '').localeCompare(b.sub || '')));
                setDeepResults(out); setDeepSearching(false);
            }
        }, 300);
        return () => { cancelled = true; clearTimeout(timer); };
    }, [filter, selectedFolder]);

    const pickFolder = async () => {
        try {
            const h = await window.showDirectoryPicker();
            window.OA_SOUND_DIR = h; setRootHandle(h);
            if (window.oaIdbSet) window.oaIdbSet('oaRootDir', h).catch(() => {}); // persist for revert
            selectFolder(h, h.name || 'root');
        } catch (e) { /* cancelled */ }
    };
    const selectFolder = async (handle, path) => {
        // Clear the current list immediately, then scan the newly picked folder.
        setFolderFiles([]); setDeepResults([]);
        setSelectedFolder(handle); setSelectedFolderPath(path || ''); setSelectedIndex(-1); setErr(''); setFilter(''); setScanning(true); setChips([]);
        const items = [], names = [], builder = makeChipBuilder();
        const onEmit = () => setChips(builder.top());   // push the growing chip list to the UI
        // Recurse every sub-folder: all names feed the chips; handles (capped) the grid.
        try { await gatherAll(handle, '', items, names, builder, onEmit, 0); }
        catch (e) { setErr('Could not read folder.'); }
        items.sort((a, b) => (a.sub === b.sub ? a.name.localeCompare(b.name) : (a.sub || '').localeCompare(b.sub || '')));
        setFolderFiles(items);
        setChips(builder.top());   // final list from EVERY filename
        setScanning(false);
        if (names.length > MAX_FILES) setErr(`Showing ${MAX_FILES} of ${names.length}${names.length >= NAME_MAX ? '+' : ''} files — filter to find the rest.`);
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
            const file = entry.file || (entry.handle && await entry.handle.getFile());
            if (!file) { setErr('File unavailable — grant folder access or re-pick the folder.'); return; }
            const folder = entry.folder != null ? entry.folder : (supportsFS ? (selectedFolderPath + (entry.sub ? '/' + entry.sub : '')) : '');
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
            if (e.key === 'Escape') { onClose(); e.preventDefault(); return; }
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
            <div onClick={(e) => e.stopPropagation()} style={{ width: '66vw', minWidth: '760px', maxWidth: '95vw', height: '80vh', display: 'flex', flexDirection: 'column', background: '#1c1c1c', border: '1px solid #f4902c', borderRadius: '6px', color: '#eee', boxShadow: '0 10px 40px rgba(0,0,0,0.6)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid #333' }}>
                    <h3 style={{ margin: 0, color: '#f4902c', textTransform: 'uppercase', letterSpacing: '1px', fontSize: '15px' }}>
                        Sound Browse{targetLabel ? ` → ${targetLabel}` : ''}
                    </h3>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#888', fontSize: '20px', cursor: 'pointer' }}>×</button>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 16px', borderBottom: '1px solid #2a2a2a', flexWrap: 'wrap' }}>
                    <div style={{ display: 'flex', border: '1px solid #444', borderRadius: '4px', overflow: 'hidden' }}>
                        <button onClick={showFiles} style={{ background: view === 'files' ? '#f4902c' : '#222', color: view === 'files' ? '#111' : '#ccc', border: 'none', padding: '5px 12px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }}>FILES</button>
                        <button onClick={showFavorites} style={{ background: view === 'favorites' ? '#f4902c' : '#222', color: view === 'favorites' ? '#111' : '#ccc', border: 'none', padding: '5px 12px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }}>★ Favorites{favorites.length ? ` (${favorites.length})` : ''}</button>
                        <button onClick={showCloud} style={{ background: view === 'cloud' ? '#f4902c' : '#222', color: view === 'cloud' ? '#111' : '#ccc', border: 'none', padding: '5px 12px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }}>☁ THE CLOUD</button>
                    </div>
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
                    {filter.trim() && <span style={{ fontSize: '11px', color: '#8ab4f8' }}>{deepSearching ? 'searching…' : `${shown.length} match${shown.length === 1 ? '' : 'es'}`}</span>}
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
                        {view === 'files' && (chips.length > 0 || scanning) && (
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
                                <div style={{ display: 'grid', gridTemplateColumns: `repeat(${COLS}, minmax(0, 1fr))`, gap: '8px' }}>
                                    {shown.map((entry, i) => (
                                        <div key={i} ref={i === selectedIndex ? selectedThumbRef : undefined} style={{ minWidth: 0 }}>
                                            <WaveThumb entry={entry} selected={i === selectedIndex} onSelect={() => selectFileByIndex(i)} scrollRootRef={gridScrollRef} />
                                        </div>
                                    ))}
                                </div>
                            ) : view === 'cloud' ? (
                                <div style={{ width: '100%', height: '100%', position: 'relative' }}>
                                    {cloudErr ? (
                                        <div style={{ color: '#ccc', fontSize: '13px', padding: '30px', textAlign: 'center', lineHeight: '1.6' }}>
                                            <div style={{ fontSize: '24px', marginBottom: '10px' }}>☁️</div>
                                            {cloudErr}
                                        </div>
                                    ) : cloudData ? (
                                        <SoundCloudView data={cloudData} rootHandle={rootHandle} onSelectFile={(entry) => {
                                            setSelected(entry);
                                            // Auto-play when selected in cloud
                                            const playIt = async () => {
                                                setPos(0);
                                                try {
                                                    const buf = await window.oaDecodeAudio(window.oaAudioCtx(), await entry.file.arrayBuffer());
                                                    setBuffer(buf);
                                                } catch(e) {}
                                            };
                                            playIt();
                                        }} />
                                    ) : (
                                        <div style={{ color: '#888', fontSize: '12px', padding: '30px', textAlign: 'center' }}>Loading cloud...</div>
                                    )}
                                </div>
                            ) : (
                                <div style={{ color: '#666', fontSize: '12px', padding: '30px', textAlign: 'center' }}>
                                    {view === 'favorites'
                                        ? (favorites.length ? 'No matching favorites.' : 'No favorites yet — open Files, pick a sound, and ☆ Favorite it.')
                                        : (deepSearching ? 'Searching all folders…' : (scanning ? 'Scanning folders…' : (files.length ? 'No matches.' : (supportsFS ? 'Select a folder on the left to see its waveforms.' : 'No files chosen yet.'))))}
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
                        <button onClick={toggleFav} disabled={!selected} title="Add/remove this file from favorites"
                            style={tbtn({ background: isFav(selected) ? '#f4902c' : '#333', color: isFav(selected) ? '#111' : '#fff', border: 'none', fontWeight: 'bold' })}>
                            {isFav(selected) ? '★ Favorited' : '☆ Favorite'}
                        </button>
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
