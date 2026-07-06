/**
 * Header: Reverb.jsx
 * Purpose: Reverb impulse-response visualizer + FIR / JFIR / CSV export.
 * Description: Renders a live reverb impulse response (time x amplitude) with an
 *   energy-decay overlay, driven by MQTT parameter topics (PreDelay, Decay/RT60,
 *   Diffusion, Size, Damping, Mix). Supports Mono / Stereo / 5.1 layouts — each
 *   channel is a decorrelated IR. Exports the IR as a .fir (the convolution kernel),
 *   the curve as CSV, and a JFIR bundle (params + per-channel FIR + curve CSV) — the
 *   5.1 case fits in one JFIR object or exports as separate .fir files.
 *
 * DSP lives in window.OaDsp (../_dsp/dsp.js); JFIR bundling in window.OaJfir
 * (../_dsp/jfir.js). Local fallbacks keep the component alive if those load late.
 *
 * Version: 26.07.06.2
 * Change Log:
 * - 2026-07-06: Initial component (Phase 1 + 2 of REVERB PLAN.MD).
 * - 2026-07-06: Phase 4 — Stereo / 5.1 multichannel IRs + JFIR export.
 */

const _revDsp = () => window.OaDsp || {};
const _revJfir = () => window.OaJfir || null;

const _revDownload = (content, filename, mime) => {
    if (window.OaDsp && window.OaDsp._downloadText) return window.OaDsp._downloadText(content, filename, mime);
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    URL.revokeObjectURL(url);
};

// Per-channel plot colors.
const REV_CH_COLORS = { M: '#f48a20', L: '#f48a20', R: '#2196F3', C: '#4CAF50', LFE: '#9C27B0', Ls: '#FFEB3B', Rs: '#F44336' };

// Normalize any channel-mode string ("5.1", "surround", "Stereo", "mono"…).
const normLayout = (s) => {
    if (s === undefined || s === null) return null;
    const t = String(s).toLowerCase().replace(/[^a-z0-9.]/g, '');
    if (t.includes('5.1') || t === '51' || t.includes('surround')) return '5.1';
    if (t.includes('stereo') || t === '2' || t === 'lr') return 'stereo';
    if (t.includes('mono') || t === '1' || t === 'm') return 'mono';
    return null;
};

const Reverb = ({ value: mqttData, config, topic }) => {
    const chartRef = React.useRef(null);
    const chartInstance = React.useRef(null);
    const useMqttLang = window.useMqttLang || (() => ['En', () => {}]);
    const [lang] = useMqttLang();

    // Latest computed params/IRs, shared with the export handlers so the buttons
    // never fire off a stale closure (same pattern as Equalization's bandsRef).
    const paramsRef = React.useRef({});
    // { layout, channels:[names], data:{name:Float64Array}, primary:Float64Array, primaryName }
    const irRef = React.useRef({ layout: 'mono', channels: ['M'], data: {}, primary: new Float64Array(0), primaryName: 'M' });

    const draggingRef = React.useRef(false);
    const lastPubRef = React.useRef(0);

    // FIR / JFIR export config. Reverb IRs are causal → default minimum phase.
    const firDefaults = config?.fir_defaults || {};
    const [firTaps, setFirTaps] = React.useState(firDefaults.taps || 4096);
    const [firSampleRate, setFirSampleRate] = React.useState(firDefaults.sample_rate || 48000);
    const [firPhase, setFirPhase] = React.useState(firDefaults.phase || 'minimum');
    const [firWindow, setFirWindow] = React.useState(firDefaults.window || 'hann');
    const [showFirDialog, setShowFirDialog] = React.useState(false);
    // Which channel layout is live (mirrors irRef.current.layout for the popover UI).
    const [layoutMode, setLayoutMode] = React.useState('mono');
    // Trace visibility toggles. The IR trace can be turned off (e.g. to read the
    // decay envelope alone). Kept in refs too so the render effect sees live values.
    const [showIR, setShowIR] = React.useState(true);
    const [showEDC, setShowEDC] = React.useState(true);
    const showIRRef = React.useRef(true);
    const showEDCRef = React.useRef(true);
    showIRRef.current = showIR;
    showEDCRef.current = showEDC;

    const title = config?.label?.[lang] || config?.label?.En || config?.title || "Reverb";

    const heightVal = config?.geometry?.height || config?.layout?.height || 400;
    const height = typeof heightVal === 'number' ? `${heightVal}px` : heightVal;
    const widthVal = config?.geometry?.width || config?.layout?.width || '100%';
    const width = typeof widthVal === 'number' ? `${widthVal}px` : widthVal;

    const messages = (window.useMqttMessages && window.useMqttMessages()) || {};
    // NB: useMqttPublish (the working hook), NOT useMqttPublisher.
    const publishFn = window.useMqttPublish ? window.useMqttPublish() : null;

    const unwrapMqtt = (v) => {
        if (v === undefined || v === null) return undefined;
        try {
            let parsed = typeof v === 'string' ? JSON.parse(v) : v;
            if (typeof parsed === 'object' && parsed !== null && parsed.value !== undefined) return parsed.value;
            return parsed;
        } catch (e) { return v; }
    };

    const topicFor = (key) => {
        if (config?.topics && config.topics[key]) return config.topics[key];
        return `OpenAir/Gui/${config?.command}/${key}`;
    };

    const readParam = (key, dflt) => {
        const raw = messages[topicFor(key)];
        const v = parseFloat(unwrapMqtt(raw));
        if (Number.isFinite(v)) return v;
        if (mqttData && typeof mqttData === 'object') {
            const mv = parseFloat(unwrapMqtt(mqttData[key]));
            if (Number.isFinite(mv)) return mv;
        }
        return dflt;
    };

    // Channel layout: MQTT Channels topic wins, else JSON config.channels, else mono.
    const readLayout = () => {
        const raw = unwrapMqtt(messages[topicFor('Channels')]);
        return normLayout(raw) || normLayout(config?.channels) || 'mono';
    };

    const FS = 48000; // preview rate; export uses the chosen firSampleRate

    // --- synthesis (shared module preferred, degenerate fallback otherwise) ---
    const synthOne = (p, fs, maxTaps, profile) => {
        const dsp = _revDsp();
        if (dsp.synthesizeIR) return dsp.synthesizeIR(p, fs, maxTaps, profile);
        const n = Math.min(maxTaps || 96000, Math.ceil((p.rt60Sec || 1.8) * fs));
        const ir = new Float64Array(n);
        const pre = Math.round((p.preDelayMs || 0) * 1e-3 * fs);
        for (let i = pre; i < n; i++) ir[i] = Math.exp(-6.9 * (i - pre) / (n - pre)) * (i % 137 === 0 ? 1 : 0.02);
        return ir;
    };

    const synthLayout = (p, fs, maxTaps, layout) => {
        const dsp = _revDsp();
        if (layout === 'mono') {
            return { layout, channels: ['M'], data: { M: synthOne(p, fs, maxTaps) } };
        }
        if (dsp.synthesizeIRMulti) return dsp.synthesizeIRMulti(p, fs, maxTaps, layout);
        // Fallback: same IR per channel (no decorrelation) so the graph isn't empty.
        const chans = (dsp.CHANNEL_LAYOUTS && dsp.CHANNEL_LAYOUTS[layout]) || ['L', 'R'];
        const data = {}; chans.forEach(ch => { data[ch] = synthOne(p, fs, maxTaps); });
        return { layout, channels: chans, data };
    };

    // --- chart init (once) ---------------------------------------------------
    const cfgKey = JSON.stringify({ title, geometry: config?.geometry });

    React.useEffect(() => {
        if (!chartRef.current || typeof echarts === 'undefined') return;
        if (!chartInstance.current) chartInstance.current = echarts.init(chartRef.current, 'dark');

        const option = {
            backgroundColor: 'transparent',
            title: { show: false },
            legend: { show: true, top: 4, right: 60, textStyle: { color: '#bcd', fontSize: 10 }, itemWidth: 12, itemHeight: 8 },
            grid: { left: 8, right: 44, top: 28, bottom: 24, containLabel: true, show: false },
            xAxis: {
                type: 'value', name: 'ms', nameLocation: 'end', min: 0,
                axisLabel: { color: '#f48a20', fontWeight: 'bold' },
                splitLine: { show: true, lineStyle: { color: '#333' } },
                axisLine: { show: false }, axisTick: { show: false }
            },
            yAxis: [
                {
                    type: 'value', min: -1, max: 1,
                    axisLabel: { color: '#f48a20', fontWeight: 'bold' },
                    splitLine: { show: true, lineStyle: { color: '#333' } },
                    axisLine: { show: false }, axisTick: { show: false }
                },
                {
                    type: 'value', min: -60, max: 0, position: 'right',
                    axisLabel: { color: '#4CAF50', fontWeight: 'bold', formatter: '{value}dB' },
                    splitLine: { show: false },
                    axisLine: { show: false }, axisTick: { show: false }
                }
            ],
            series: [
                { name: 'IR', type: 'line', data: [], yAxisIndex: 0, lineStyle: { color: '#f48a20', width: 1 }, itemStyle: { color: '#f48a20' }, showSymbol: false, animation: false, z: 2 },
                { name: 'EDC', type: 'line', data: [], yAxisIndex: 1, lineStyle: { color: '#4CAF50', width: 2 }, itemStyle: { color: '#4CAF50' }, showSymbol: false, animation: false, z: 3 }
            ]
        };
        chartInstance.current.setOption(option, { notMerge: true });

        const handleResize = () => chartInstance.current?.resize();
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, [cfgKey, height, width, lang]);

    // --- live update: read params -> synth -> plot + handles -----------------
    React.useEffect(() => {
        if (!chartInstance.current) return;
        try {
            const layout = readLayout();
            const p = {
                preDelayMs: readParam('PreDelay', 20),
                rt60Sec:    readParam('Decay', 1.8),
                diffusion:  readParam('Diffusion', 0.7),
                size:       readParam('Size', 0.5),
                damping:    readParam('Damping', 0.3),
                mix:        readParam('Mix', 100),
                channels:   layout,
            };

            const previewMax = Math.min(96000, Math.ceil(p.rt60Sec * FS) + Math.round(p.preDelayMs * 1e-3 * FS) + 1);
            const multi = synthLayout(p, FS, previewMax, layout);
            const primaryName = multi.channels[0];
            const primary = multi.data[primaryName];

            paramsRef.current = p;
            irRef.current = { layout, channels: multi.channels, data: multi.data, primary, primaryName };
            if (layout !== layoutMode) setLayoutMode(layout);

            const dsp = _revDsp();
            const msPerSample = 1000 / FS;
            const decN = (layout === 'mono') ? 3000 : 1500; // lighter per channel when many

            // Auto-scale amplitude axis to the max peak across channels (computed even
            // when the IR trace is hidden, so the axis + Pre-Delay handle stay sane).
            let peak = 0;
            const series = [];
            multi.channels.forEach((ch) => {
                const ir = multi.data[ch];
                const dec = dsp.decimate ? dsp.decimate(ir, decN) : Array.from(ir).map((v, i) => ({ i, v }));
                for (let k = 0; k < dec.length; k++) { const a = Math.abs(dec[k].v); if (a > peak) peak = a; }
                if (!showIRRef.current) return; // IR trace toggled off
                const data = dec.map(pt => [+(pt.i * msPerSample).toFixed(3), +pt.v.toFixed(6)]);
                const color = REV_CH_COLORS[ch] || '#ccc';
                series.push({
                    name: (layout === 'mono') ? 'IR' : ch, type: 'line', data, yAxisIndex: 0,
                    lineStyle: { color, width: 1 }, itemStyle: { color }, showSymbol: false, animation: false, z: 2
                });
            });
            const yAmp = Math.max(0.01, peak * 1.1);

            // EDC of the primary channel on the right axis (also toggleable).
            if (showEDCRef.current) {
                const edcFull = dsp.energyDecayCurve ? dsp.energyDecayCurve(primary) : null;
                let edcData = [];
                if (edcFull) {
                    const dec = dsp.decimate ? dsp.decimate(primary, decN) : Array.from(primary).map((v, i) => ({ i, v }));
                    edcData = dec.map(pt => [+(pt.i * msPerSample).toFixed(3), +edcFull[pt.i].toFixed(3)]);
                }
                series.push({
                    name: 'EDC', type: 'line', data: edcData, yAxisIndex: 1,
                    lineStyle: { color: '#8f8', width: 2, type: 'dashed' }, itemStyle: { color: '#8f8' },
                    showSymbol: false, animation: false, z: 3
                });
            }

            const totalMs = primary.length * msPerSample;

            chartInstance.current.setOption({
                xAxis: { max: +totalMs.toFixed(1) },
                yAxis: [{ min: -yAmp, max: yAmp }, {}],
                series
            }, { replaceMerge: ['series'] });

            // Draggable handles (operate on params; axis-based finders are robust to
            // however many channel series are present).
            setTimeout(() => {
                if (!chartInstance.current || draggingRef.current) return;
                const graphics = [];

                const posPre = chartInstance.current.convertToPixel({ xAxisIndex: 0, yAxisIndex: 0 }, [p.preDelayMs, 0]);
                if (posPre) {
                    graphics.push(makeHandle('rev_predelay', posPre, '#f48a20', (self) => {
                        const pt = chartInstance.current.convertFromPixel({ xAxisIndex: 0, yAxisIndex: 0 }, [self.x, self.y]);
                        return { PreDelay: +Math.max(0, Math.min(200, pt[0])).toFixed(1) };
                    }));
                }

                const rt60Ms = p.rt60Sec * 1000;
                const posDecay = chartInstance.current.convertToPixel({ xAxisIndex: 0, yAxisIndex: 1 }, [Math.min(rt60Ms, totalMs), -60]);
                if (posDecay) {
                    graphics.push(makeHandle('rev_decay', posDecay, '#4CAF50', (self) => {
                        const pt = chartInstance.current.convertFromPixel({ xAxisIndex: 0, yAxisIndex: 1 }, [self.x, self.y]);
                        return { Decay: +Math.max(0.1, Math.min(10, pt[0] / 1000)).toFixed(2) };
                    }));
                }

                chartInstance.current.setOption({ graphic: graphics });
            }, 50);
        } catch (e) {
            console.error('[Reverb]', e);
        }
    }, [messages, config?.command, mqttData, showIR, showEDC]);

    const makeHandle = (id, pos, color, compute) => ({
        type: 'circle', id, position: pos, shape: { r: 11 },
        style: { fill: color, stroke: '#fff', lineWidth: 2, shadowBlur: 4, shadowColor: '#000' },
        invisible: false, draggable: true, z: 100,
        ondragstart: function () { draggingRef.current = true; },
        ondrag: function () {
            draggingRef.current = true;
            const now = Date.now();
            if (now - lastPubRef.current >= 40) { lastPubRef.current = now; publishUpdate(compute(this)); }
        },
        ondragend: function () {
            publishUpdate(compute(this));
            setTimeout(() => { draggingRef.current = false; }, 60);
        }
    });

    const publishUpdate = (upd) => {
        if (!publishFn || !upd) return;
        Object.keys(upd).forEach((key) => publishFn(topicFor(key), { value: upd[key] }));
    };

    // --- FIR windowing (shared with export) ----------------------------------
    // Apply the chosen window/phase taper to a synthesized (causal) IR in place.
    const applyFirWindow = (ir) => {
        const dsp = _revDsp();
        if (!dsp._windowVal || firWindow === 'rect') return ir;
        const N = ir.length;
        if (firPhase === 'linear') {
            for (let n = 0; n < N; n++) ir[n] *= dsp._windowVal(firWindow, n, N);
        } else {
            // energy lives at the front → taper the tail half only
            for (let n = 0; n < N; n++) ir[n] *= dsp._windowVal(firWindow, (N - 1) + n, 2 * N - 1);
        }
        return ir;
    };

    // Re-render every channel of the current layout at the chosen fs/taps, windowed.
    const renderFirData = () => {
        const p = paramsRef.current || {};
        const fs = parseInt(firSampleRate, 10);
        const taps = parseInt(firTaps, 10);
        const layout = irRef.current.layout || 'mono';
        const multi = synthLayout(p, fs, taps, layout);
        const data = {};
        multi.channels.forEach((ch) => { data[ch] = applyFirWindow(multi.data[ch]); });
        return { channels: multi.channels, data, taps, fs, layout };
    };

    // --- curve CSV (shared with CSV button and JFIR bundle) ------------------
    const buildCurveCsv = () => {
        const ir = irRef.current.primary || new Float64Array(0);
        const dsp = _revDsp();
        const edc = dsp.energyDecayCurve ? dsp.energyDecayCurve(ir) : new Float64Array(ir.length);
        const msPerSample = 1000 / FS;
        let csv = "TimeMs,Amplitude,DecayDb\n";
        for (let n = 0; n < ir.length; n++) {
            csv += `${(n * msPerSample).toFixed(4)},${ir[n].toFixed(8)},${(edc[n] || 0).toFixed(3)}\n`;
        }
        return { columns: ["TimeMs", "Amplitude", "DecayDb"], csv };
    };

    // --- exports -------------------------------------------------------------
    const handleExportFIR = () => {
        // Primary channel only → plain .fir (the convolution kernel).
        const rendered = renderFirData();
        const primary = rendered.data[rendered.channels[0]];
        let firContent = '';
        for (let i = 0; i < primary.length; i++) firContent += primary[i].toFixed(10) + '\n';
        _revDownload(firContent, 'reverb_ir.fir', 'text/plain;charset=utf-8;');
        setShowFirDialog(false);
    };

    const buildJfir = () => {
        const rendered = renderFirData();
        const jfir = _revJfir();
        const meta = {
            kind: 'reverb',
            label: title,
            sampleRate: rendered.fs,
            parameters: paramsRef.current || {},
            fir: { taps: rendered.taps, phase: firPhase, window: firWindow, channels: rendered.channels, data: rendered.data },
            curve: buildCurveCsv(),
        };
        return jfir ? jfir.build(meta) : { format: 'JFIR', version: 1, ...meta };
    };

    const handleExportJFIR = () => {
        const jfir = _revJfir();
        const obj = buildJfir();
        if (jfir) jfir.download(obj);
        else _revDownload(JSON.stringify(obj, null, 2), 'reverb.jfir', 'application/json;charset=utf-8;');
        setShowFirDialog(false);
    };

    const handleExportSeparateFir = () => {
        const jfir = _revJfir();
        const obj = buildJfir();
        if (jfir) { jfir.downloadSeparateFir(obj); }
        else {
            (obj.fir.channels || []).forEach((ch) => {
                const taps = obj.fir.data[ch]; if (!taps) return;
                let s = ''; for (let i = 0; i < taps.length; i++) s += (+taps[i]).toFixed(10) + '\n';
                const suffix = obj.fir.channels.length === 1 ? '' : ('_' + ch);
                _revDownload(s, `reverb_ir${suffix}.fir`, 'text/plain;charset=utf-8;');
            });
        }
        setShowFirDialog(false);
    };

    const handleExportCSV = () => {
        const { csv } = buildCurveCsv();
        _revDownload(csv, 'reverb_curve.csv', 'text/csv;charset=utf-8;');
    };

    // --- styles (match Equalization's toolbar) -------------------------------
    const ctrlLabel = { display: 'flex', flexDirection: 'column', fontSize: '9px', color: '#bcd', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.5px', gap: '2px' };
    const ctrlSelect = { fontSize: '11px', padding: '2px 4px', border: '1px solid #667', borderRadius: '3px', background: '#e8eef1', color: '#223' };
    const iconBtn = { fontSize: '10px', fontWeight: 'bold', padding: '3px 8px', border: '1px solid rgba(255,255,255,0.25)', borderRadius: '3px', background: 'rgba(40,44,52,0.75)', color: '#fff', cursor: 'pointer', backdropFilter: 'blur(2px)' };
    // Active-state pill (a trace toggle that is currently ON).
    const iconBtnOn = { ...iconBtn, background: 'rgba(244,138,32,0.85)', color: '#1a1a1a', border: '1px solid rgba(255,255,255,0.5)' };

    const isMulti = layoutMode !== 'mono';
    const chanList = (_revDsp().CHANNEL_LAYOUTS && _revDsp().CHANNEL_LAYOUTS[layoutMode]) || ['M'];

    return (
        <div style={{ position: 'relative', width: '100%', padding: '2px', backgroundColor: 'transparent', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.15)', boxSizing: 'border-box' }}>
            <div ref={chartRef} style={{ width: '100%', height, position: 'relative' }} />

            {/* Trace toggles + export buttons — top-right corner of the graph */}
            <div style={{ position: 'absolute', top: 6, right: 8, display: 'flex', gap: 6, zIndex: 20 }}>
                <button style={showIR ? iconBtnOn : iconBtn} title="Show / hide the impulse response trace" onClick={() => setShowIR(v => !v)}>IR</button>
                <button style={showEDC ? iconBtnOn : iconBtn} title="Show / hide the energy-decay curve" onClick={() => setShowEDC(v => !v)}>EDC</button>
                <button style={iconBtn} title="Export impulse response / JFIR bundle…" onClick={() => setShowFirDialog(v => !v)}>FIR ▾</button>
                <button style={iconBtn} title="Export impulse response + decay curve as CSV" onClick={handleExportCSV}>CSV</button>
            </div>

            {/* FIR / JFIR configuration popover */}
            {showFirDialog && (
                <div style={{ position: 'absolute', top: 34, right: 8, zIndex: 30, background: 'rgba(24,26,30,0.97)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', padding: '10px 12px', boxShadow: '0 6px 20px rgba(0,0,0,0.5)', display: 'flex', flexDirection: 'column', gap: '8px', minWidth: '186px' }}>
                    <div style={{ fontSize: '11px', fontWeight: 'bold', color: '#fff', letterSpacing: '0.5px' }}>Reverb IR / JFIR Export</div>
                    <div style={{ fontSize: '9px', color: '#9ab', fontWeight: 'bold' }}>
                        Layout: {layoutMode.toUpperCase()} · {chanList.join(' ')}
                    </div>
                    <label style={ctrlLabel}>
                        Taps
                        <select style={ctrlSelect} value={firTaps} onChange={(e) => setFirTaps(parseInt(e.target.value, 10))}>
                            {[2048, 4096, 8192, 16384, 32768, 65536].map(n => (<option key={n} value={n}>{n}</option>))}
                        </select>
                    </label>
                    <label style={ctrlLabel}>
                        Sample Rate
                        <select style={ctrlSelect} value={firSampleRate} onChange={(e) => setFirSampleRate(parseInt(e.target.value, 10))}>
                            {[44100, 48000, 88200, 96000, 192000].map(n => (<option key={n} value={n}>{n >= 1000 ? (n / 1000) + ' kHz' : n}</option>))}
                        </select>
                    </label>
                    <label style={ctrlLabel}>
                        Phase
                        <select style={ctrlSelect} value={firPhase} onChange={(e) => setFirPhase(e.target.value)}>
                            <option value="minimum">Minimum (causal)</option>
                            <option value="linear">Linear</option>
                        </select>
                    </label>
                    <label style={ctrlLabel}>
                        Window
                        <select style={ctrlSelect} value={firWindow} onChange={(e) => setFirWindow(e.target.value)}>
                            <option value="hann">Hann</option>
                            <option value="hamming">Hamming</option>
                            <option value="blackman">Blackman</option>
                            <option value="kaiser">Kaiser</option>
                            <option value="rect">Rectangular</option>
                        </select>
                    </label>
                    <div style={{ display: 'flex', gap: '6px', marginTop: '2px', flexWrap: 'wrap' }}>
                        <button style={{ ...iconBtn, flex: 1, padding: '5px', background: '#2f6f3f' }} title="Single JSON bundle: params + per-channel FIR + curve CSV" onClick={handleExportJFIR}>JFIR</button>
                        <button style={{ ...iconBtn, padding: '5px 8px' }} title={isMulti ? 'Primary channel only, plain .fir' : 'Plain .fir'} onClick={handleExportFIR}>FIR</button>
                    </div>
                    {isMulti && (
                        <button style={{ ...iconBtn, padding: '5px 8px' }} title="One .fir file per channel" onClick={handleExportSeparateFir}>
                            {chanList.length}× separate .fir
                        </button>
                    )}
                    <button style={{ ...iconBtn, padding: '4px 8px' }} onClick={() => setShowFirDialog(false)}>Cancel</button>
                </div>
            )}
        </div>
    );
};

window.Reverb = Reverb;
