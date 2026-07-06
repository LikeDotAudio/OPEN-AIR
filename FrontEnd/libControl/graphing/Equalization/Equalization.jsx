/**
 * Header: Equalization.jsx
 * Purpose: Equalization component or utility.
 * Description: Handles logic and rendering for Equalization component or utility.
 * 
 * Version: 26.07.06.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 * - 2026-07-06: FIR export now configurable — Taps/Sample Rate/Phase (linear or
 *   minimum)/Window dropdowns; frequency-sampling generator backed by a radix-2
 *   FFT (replaces the hardcoded 1024-tap O(N^2) export). CSV export unchanged.
 */

// Equalization Graph Component
// Renders a specialized frequency equalization curve based on ECharts.

// ---------------------------------------------------------------------------
// DSP helpers (module scope so both the live curve and the FIR export share them)
// ---------------------------------------------------------------------------

// Magnitude (dB) of a single band at frequency f. Bell/shelf use analog Bode
// transfer functions (sample-rate independent); HP/LP use a digital biquad and
// therefore depend on fs (the export sample rate).
const getBiquadGainDB = (f, fc, Q, gainDB, type = 'peaking', enabled = true, fs = 48000) => {
    if (!enabled) return 0;

    if (type === 'lowshelf' || type === 'highshelf' || type === 'peaking') {
        if (gainDB === 0) return 0;
        const V = Math.pow(10, gainDB / 20); // Linear amplitude
        const x = f / fc;                    // Normalized frequency ratio
        let magnitudeSq = 1;

        if (type === 'lowshelf') {
            magnitudeSq = (Math.pow(x, 2) + Math.pow(V, 2)) / (Math.pow(x, 2) + 1);
        } else if (type === 'highshelf') {
            magnitudeSq = (Math.pow(V * x, 2) + 1) / (Math.pow(x, 2) + 1);
        } else if (type === 'peaking') {
            const term1 = Math.pow(1 - Math.pow(x, 2), 2);
            const numerator = term1 + Math.pow((V / Q) * x, 2);
            const denominator = term1 + Math.pow((1 / Q) * x, 2);
            magnitudeSq = numerator / denominator;
        }
        return 10 * Math.log10(magnitudeSq);
    }

    // Standard digital biquad for lowpass and highpass
    const w0 = 2 * Math.PI * fc / fs;
    const alpha = Math.sin(w0) / (2 * Q);
    let b0, b1, b2, a0, a1, a2;

    if (type === 'highpass') {
        b0 =  (1 + Math.cos(w0)) / 2;
        b1 = -(1 + Math.cos(w0));
        b2 =  (1 + Math.cos(w0)) / 2;
        a0 =   1 + alpha;
        a1 =  -2 * Math.cos(w0);
        a2 =   1 - alpha;
    } else if (type === 'lowpass') {
        b0 =  (1 - Math.cos(w0)) / 2;
        b1 =   1 - Math.cos(w0);
        b2 =  (1 - Math.cos(w0)) / 2;
        a0 =   1 + alpha;
        a1 =  -2 * Math.cos(w0);
        a2 =   1 - alpha;
    } else {
        return 0; // Fallback
    }

    const M0 = b0 / a0, M1 = b1 / a0, M2 = b2 / a0;
    const P1 = a1 / a0, P2 = a2 / a0;

    const w = 2 * Math.PI * f / fs;
    const cos_w = Math.cos(w);
    const cos_2w = Math.cos(2 * w);

    const num = M0*M0 + M1*M1 + M2*M2 + 2*(M0*M1 + M1*M2)*cos_w + 2*M0*M2*cos_2w;
    const den = 1 + P1*P1 + P2*P2 + 2*(P1 + P1*P2)*cos_w + 2*P2*cos_2w;

    return 10 * Math.log10(num / den);
};

// In-place iterative radix-2 FFT. Length must be a power of two.
// inverse=true performs the IFFT (and divides by N).
const _fft = (re, im, inverse) => {
    const n = re.length;
    if (n <= 1) return;
    // Bit-reversal permutation
    for (let i = 1, j = 0; i < n; i++) {
        let bit = n >> 1;
        for (; j & bit; bit >>= 1) j ^= bit;
        j ^= bit;
        if (i < j) {
            const tr = re[i]; re[i] = re[j]; re[j] = tr;
            const ti = im[i]; im[i] = im[j]; im[j] = ti;
        }
    }
    for (let len = 2; len <= n; len <<= 1) {
        const ang = (inverse ? 2 : -2) * Math.PI / len;
        const wr = Math.cos(ang), wi = Math.sin(ang);
        for (let i = 0; i < n; i += len) {
            let cwr = 1, cwi = 0;
            for (let k = 0; k < len / 2; k++) {
                const a = i + k, b = i + k + len / 2;
                const xr = re[b] * cwr - im[b] * cwi;
                const xi = re[b] * cwi + im[b] * cwr;
                re[b] = re[a] - xr; im[b] = im[a] - xi;
                re[a] += xr;        im[a] += xi;
                const ncwr = cwr * wr - cwi * wi;
                cwi = cwr * wi + cwi * wr;
                cwr = ncwr;
            }
        }
    }
    if (inverse) {
        for (let i = 0; i < n; i++) { re[i] /= n; im[i] /= n; }
    }
};

// Modified Bessel function I0 (series) for the Kaiser window.
const _besselI0 = (x) => {
    let sum = 1, term = 1;
    for (let k = 1; k < 30; k++) {
        term *= (x * x) / (4 * k * k);
        sum += term;
        if (term < 1e-12 * sum) break;
    }
    return sum;
};

// Symmetric window value at sample n of a length-N window.
const _windowVal = (type, n, N) => {
    const M = N - 1;
    if (M <= 0) return 1;
    switch (type) {
        case 'rect':     return 1;
        case 'hann':     return 0.5 - 0.5 * Math.cos(2 * Math.PI * n / M);
        case 'hamming':  return 0.54 - 0.46 * Math.cos(2 * Math.PI * n / M);
        case 'blackman': return 0.42 - 0.5 * Math.cos(2 * Math.PI * n / M) + 0.08 * Math.cos(4 * Math.PI * n / M);
        case 'kaiser': {
            const beta = 8.0;
            const r = (2 * n / M) - 1; // -1..1
            return _besselI0(beta * Math.sqrt(Math.max(0, 1 - r * r))) / _besselI0(beta);
        }
        default: return 1;
    }
};

// Turn the EQ band set into an FIR impulse response using the frequency
// sampling method. opts = { taps, sampleRate, phase, window }.
//   phase 'linear'  -> exact symmetric taps (zero phase distortion, N/2 latency)
//   phase 'minimum' -> real-cepstrum method (no pre-ringing, mimics analog)
const generateFIR = (bands, opts) => {
    const N = opts.taps;          // number of taps (power of two)
    const fs = opts.sampleRate;
    const phase = opts.phase;
    const win = opts.window;

    // Sample the target magnitude on N bins, enforcing Hermitian symmetry so
    // the IFFT is real-valued.
    const mag = new Float64Array(N);
    for (let k = 0; k <= N / 2; k++) {
        const f = (k * fs) / N;
        let db = 0;
        if (f > 0) {
            for (let bi = 0; bi < bands.length; bi++) {
                const b = bands[bi];
                db += getBiquadGainDB(f, b.freq, b.q, b.gain, b.type, b.enabled, fs);
            }
        }
        const amp = Math.pow(10, db / 20);
        mag[k] = amp;
        if (k > 0 && k < N / 2) mag[N - k] = amp;
    }

    const re = new Float64Array(N);
    const im = new Float64Array(N);
    const ir = new Float64Array(N);

    if (phase === 'minimum') {
        // Real-cepstrum -> minimum phase reconstruction.
        const floor = 1e-6; // guard against log(0) in deep cuts
        const cRe = new Float64Array(N);
        const cIm = new Float64Array(N);
        for (let k = 0; k < N; k++) { cRe[k] = Math.log(Math.max(mag[k], floor)); cIm[k] = 0; }
        _fft(cRe, cIm, true); // cepstrum
        // Causal weighting (fold anti-causal energy onto the causal side)
        for (let k = 0; k < N; k++) {
            const w = (k === 0 || k === N / 2) ? 1 : (k < N / 2 ? 2 : 0);
            cRe[k] *= w; cIm[k] *= w;
        }
        _fft(cRe, cIm, false); // complex log spectrum
        for (let k = 0; k < N; k++) {
            const ex = Math.exp(cRe[k]);
            re[k] = ex * Math.cos(cIm[k]);
            im[k] = ex * Math.sin(cIm[k]);
        }
        _fft(re, im, true); // minimum-phase impulse (energy front-loaded at n=0)
        // Taper only the tail (energy lives at the start of a min-phase IR).
        for (let n = 0; n < N; n++) {
            const w = (win === 'rect') ? 1 : _windowVal(win, (N - 1) + n, 2 * N - 1);
            ir[n] = re[n] * w;
        }
    } else {
        // Linear phase: real symmetric taps, centered via a circular shift.
        for (let k = 0; k < N; k++) { re[k] = mag[k]; im[k] = 0; }
        _fft(re, im, true);
        for (let n = 0; n < N; n++) {
            const src = (n - N / 2 + N) % N; // peak lands at n = N/2
            ir[n] = re[src] * _windowVal(win, n, N);
        }
    }

    return ir;
};

// Trigger a browser download for generated text content.
const _downloadText = (content, filename, mime) => {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
};

// Inline comment: Logic for Equalization
const Equalization = ({ value: mqttData, config, topic }) => {
    const chartRef = React.useRef(null);
    const chartInstance = React.useRef(null);
    const useMqttLang = window.useMqttLang || (() => ['En', () => {}]);
    const [lang] = useMqttLang();

    // Latest computed curve data, shared with the export handlers (the heavy
    // MQTT effect updates these so the buttons never work off a stale closure).
    const bandsRef = React.useRef([]);
    const totalDataRef = React.useRef([]);

    // FIR export settings (exposed as dropdowns above the graph). Defaults match
    // the previous hardcoded export: 1024 taps @ 48kHz, linear phase, Hamming.
    const [firTaps, setFirTaps] = React.useState(1024);
    const [firSampleRate, setFirSampleRate] = React.useState(48000);
    const [firPhase, setFirPhase] = React.useState('linear');
    const [firWindow, setFirWindow] = React.useState('hamming');

    const handleExportFIR = () => {
        const bands = bandsRef.current || [];
        const ir = generateFIR(bands, {
            taps: parseInt(firTaps, 10),
            sampleRate: parseInt(firSampleRate, 10),
            phase: firPhase,
            window: firWindow
        });
        let firContent = '';
        for (let i = 0; i < ir.length; i++) firContent += ir[i].toFixed(10) + '\n';
        _downloadText(firContent, 'eq_filter.fir', 'text/plain;charset=utf-8;');
    };

    const handleExportCSV = () => {
        let csvContent = "Freq,Gain\n";
        (totalDataRef.current || []).forEach(row => {
            csvContent += `${row[0]},${row[1]}\n`;
        });
        _downloadText(csvContent, 'eq_curve.csv', 'text/csv;charset=utf-8;');
    };

    const title = config?.label?.[lang] || config?.label?.En || config?.title || "Equalizer";
    
    // Geometry
    const heightVal = config?.geometry?.height || config?.layout?.height || 350;
    const height = typeof heightVal === 'number' ? `${heightVal}px` : heightVal;
    
    const widthVal = config?.geometry?.width || config?.layout?.width || '100%';
    const width = typeof widthVal === 'number' ? `${widthVal}px` : widthVal;

    // Data Processing
    const parseCsv = (csvString) => {
        if (!csvString) return [];
        const lines = csvString.split('\n');
        const data = [];
        for (let i = 1; i < lines.length; i++) { 
            const trimmedLine = lines[i].trim();
            if (!trimmedLine) continue; 
            const values = trimmedLine.split(',');
            if (values.length >= 2) {
                const x = parseFloat(values[0]);
                const y = parseFloat(values[1]);
                if (!isNaN(x) && !isNaN(y)) data.push([x, y]);
            }
        }
        return data;
    };

    const cfgKey = JSON.stringify({ datasets: config?.datasets, title });

    React.useEffect(() => {
        if (!chartRef.current || typeof echarts === 'undefined') return;

        if (!chartInstance.current) {
            chartInstance.current = echarts.init(chartRef.current, 'dark');
        }

        const primaryDataset = (config?.datasets || [])[0];
        // Generate a sample smooth curve if no data provided
        let defaultData = [];
        if (primaryDataset?.initial_csv_data) {
            defaultData = parseCsv(primaryDataset.initial_csv_data);
        } else {
            // Zero setting if no data provided
            defaultData = [
                [20, 0], [50, 0], [100, 0], [200, 0], [500, 0], 
                [1000, 0], [2000, 0], [5000, 0], [10000, 0], [20000, 0]
            ];
        }

        const option = {
            backgroundColor: '#050505',
            title: {
                text: title,
                left: 10,
                top: 10,
                textStyle: { color: '#888', fontSize: 12, fontWeight: 'normal' }
            },
            grid: {
                left: '8%',
                right: '5%',
                top: '15%',
                bottom: '15%',
                containLabel: true,
                show: false,
            },
            xAxis: {
                type: 'log',
                logBase: 10,
                min: 20,
                max: 20000,
                axisLabel: {
                    formatter: function (value) {
                        if (value === 20) return '20';
                        if (value === 100) return '100';
                        if (value === 1000) return '1k';
                        if (value === 10000) return '10k';
                        if (value === 20000) return '20k';
                        return '';
                    },
                    color: '#f48a20',
                    fontWeight: 'bold'
                },
                splitLine: { show: true, lineStyle: { color: '#333' } },
                minorSplitLine: { show: true, lineStyle: { color: '#2a2a2a', width: 1 } },
                axisLine: { show: false },
                axisTick: { show: false }
            },
            yAxis: {
                type: 'value',
                min: -32,
                max: 32,
                interval: 8,
                axisLabel: {
                    color: '#f48a20',
                    fontWeight: 'bold'
                },
                splitLine: { show: true, lineStyle: { color: '#333' } },
                minorSplitLine: { show: true, lineStyle: { color: '#2a2a2a', width: 1 } },
                axisLine: { show: false },
                axisTick: { show: false }
            },
            series: [
                {
                    name: '0dB Ref',
                    type: 'line',
                    data: [[20, 0], [20000, 0]],
                    lineStyle: { color: '#f48a20', width: 1, type: 'dashed' },
                    showSymbol: false,
                    animation: false
                },
                {
                    name: 'EQ Curve',
                    type: 'line',
                    data: defaultData,
                    smooth: true,
                    lineStyle: { color: '#f48a20', width: 2 },
                    itemStyle: { color: '#f48a20' },
                    showSymbol: false,
                    animationDuration: 300
                }
            ],
            graphic: [
                {
                    type: 'text',
                    right: '15%',
                    bottom: '5%',
                    style: {
                        text: 'LoCut  LF  LMF  HMF  HF  HiCut',
                        fill: '#f48a20',
                        fontSize: 11,
                        fontWeight: 'bold'
                    }
                },
                {
                    type: 'text',
                    right: '5%',
                    top: '8%',
                    style: {
                        text: 'On',
                        fill: '#f48a20',
                        fontSize: 12,
                        fontWeight: 'bold'
                    }
                }
            ]
        };

        chartInstance.current.setOption(option, { notMerge: true });
        
        const handleResize = () => chartInstance.current?.resize();
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, [cfgKey, height, width, lang]);

    const messages = (window.useMqttMessages && window.useMqttMessages()) || {};
    const publishFn = window.useMqttPublish ? window.useMqttPublish() : null;

    // Handle real-time MQTT updates
    React.useEffect(() => {
        if (!chartInstance.current) return;
        try {
            const bands = [];
            const baseTopic = `OpenAir/Gui/${config?.command}`;

            const unwrapMqtt = (v) => {
                if (v === undefined || v === null) return undefined;
                try {
                    let parsed = typeof v === 'string' ? JSON.parse(v) : v;
                    if (typeof parsed === 'object' && parsed !== null && parsed.value !== undefined) return parsed.value;
                    return parsed;
                } catch(e) { return v; }
            };

            const parseBand = (key, bandData, ltpParsed, qParsed) => {
                let freq = unwrapMqtt(bandData?.Freq) ?? unwrapMqtt(bandData?.freq) ?? unwrapMqtt(bandData?.Frequency) ?? unwrapMqtt(bandData?.frequency);
                let gain = unwrapMqtt(bandData?.Gain) ?? unwrapMqtt(bandData?.gain);
                let q = unwrapMqtt(bandData?.Q) ?? unwrapMqtt(bandData?.q);
                
                if (freq === undefined && ltpParsed) freq = ltpParsed.value;
                if (gain === undefined && ltpParsed && ltpParsed.rotValue !== undefined) gain = ltpParsed.rotValue;
                if (q === undefined && qParsed) q = qParsed.value !== undefined ? qParsed.value : qParsed;
                
                freq = parseFloat(freq);
                gain = parseFloat(gain);
                q = parseFloat(q) || 1.0;
                
                let type = 'peaking';
                if (key.toLowerCase().includes('locut') || key.toLowerCase().includes('hpf')) type = 'highpass';
                if (key.toLowerCase().includes('hicut') || key.toLowerCase().includes('lpf')) type = 'lowpass';

                const lowShelf = unwrapMqtt(messages[`OpenAir/Gui/EQ_Params/Low/Shelf`]);
                const highShelf = unwrapMqtt(messages[`OpenAir/Gui/EQ_Params/High/Shelf`]);

                // Shelf overrides
                if (key.toLowerCase() === 'low' && (lowShelf == 1 || lowShelf === true)) {
                    type = 'lowshelf';
                }
                if (key.toLowerCase() === 'high' && (highShelf == 1 || highShelf === true)) {
                    type = 'highshelf';
                }
                
                // Filters like HP/LP often don't have a gain parameter
                if (type === 'highpass' || type === 'lowpass') {
                    if (isNaN(gain)) gain = 0;
                }
                
                let enabled = false;
                if (type === 'highpass') enabled = freq > 20.5; // Enable if slightly above 20Hz
                else if (type === 'lowpass') enabled = freq < 19999; // Enable if slightly below 20kHz
                else enabled = gain !== 0;

                if (!isNaN(freq) && !isNaN(gain) && !isNaN(q)) {
                    bands.push({ name: key, freq, gain, q, type, enabled });
                }
            };

            // 1. Scrape the raw messages dictionary for any sub-topics matching the base topic
            let bandKeys = ['LoCut', 'Low', 'LowMid', 'Mid', 'HighMid', 'High', 'HiCut'];
            let getBaseTopic = (key) => `${baseTopic}/${key}`;
            
            if (config?.topics) {
                bandKeys = Object.keys(config.topics);
                getBaseTopic = (key) => config.topics[key];
            }

            bandKeys.forEach(key => {
                const topic = getBaseTopic(key);
                const ltpMsg = messages[topic];
                const qMsg = messages[`${topic}/Q`];
                let ltpParsed = null;
                let qParsed = null;
                
                if (ltpMsg) {
                    try { ltpParsed = JSON.parse(ltpMsg); } catch(e) {}
                }
                if (qMsg) {
                    try { qParsed = JSON.parse(qMsg); } catch(e) {}
                }
                
                if (ltpParsed || qParsed) {
                    parseBand(key, {}, ltpParsed, qParsed);
                }
            });

            // 2. Fallback to aggregated mqttData (e.g., if generated by backend engine)
            if (bands.length === 0 && typeof mqttData === 'string' && mqttData.includes(',')) {
                const newData = parseCsv("x,y\\n" + mqttData);
                if (newData.length) {
                    chartInstance.current.setOption({
                        series: [{ data: [[20,0],[20000,0]] }, { data: newData }]
                    });
                    return; // Early return for static CSV payload
                }
            } else if (bands.length === 0 && typeof mqttData === 'object' && mqttData !== null) {
                for (const key in mqttData) {
                    const band = mqttData[key];
                    if (band && typeof band === 'object') {
                        parseBand(key, band);
                    }
                }
            }

            // At this point we have our parsed bands. Now generate the points.
            console.log(`[EQ] bands.length=${bands.length}, mqttData type=${typeof mqttData}`);
            console.log('[EQ] Parsed Bands Data:', JSON.stringify(bands));
            if (true) {
                    const steps = 500; // Using 500 points to match the user's Excel precision
                    const minF = Math.log10(20);
                    const maxF = Math.log10(20000);
                    
                    const totalData = [];
                    const bandDataArray = bands.map(() => []);

                    for (let i = 0; i <= steps; i++) {
                        const f = Math.pow(10, minF + (maxF - minF) * (i / steps));
                        let totalGain = 0;
                        
                        bands.forEach((b, bIdx) => {
                            const bandGain = getBiquadGainDB(f, b.freq, b.q, b.gain, b.type, b.enabled);
                            totalGain += bandGain;
                            bandDataArray[bIdx].push([parseFloat(f.toFixed(1)), parseFloat(bandGain.toFixed(2))]);
                        });
                        
                        totalData.push([parseFloat(f.toFixed(1)), parseFloat(totalGain.toFixed(2))]);
                    }
                    
                    const getBandColor = (name) => {
                        const defaultColors = {
                            'Low': '#4CAF50',
                            'LowMid': '#FFEB3B',
                            'Mid': '#FFEB3B',
                            'HighMid': '#FFEB3B',
                            'High': '#F44336',
                            'HiCut': '#795548',
                            'LoCut': '#BDBDBD'
                        };
                        return defaultColors[name] || '#FFFFFF';
                    };
                    
                    const series = [
                        {
                            name: '0dB Ref',
                            type: 'line',
                            data: [[20, 0], [20000, 0]],
                            lineStyle: { color: '#888', width: 1, type: 'dashed' },
                            showSymbol: false,
                            animation: false,
                            z: 1
                        }
                    ];
                    
                    bands.forEach((b, i) => {
                        const bandColor = getBandColor(b.name);
                        series.push({
                            name: b.name || `Band ${i+1}`,
                            type: 'line',
                            data: bandDataArray[i],
                            smooth: true,
                            lineStyle: { color: bandColor, width: 1 },
                            itemStyle: { color: bandColor },
                            areaStyle: {
                                color: bandColor,
                                opacity: 0.15
                            },
                            showSymbol: false,
                            animation: false,
                            z: 2
                        });
                    });
                    
                    series.push({
                        name: 'Total EQ Curve',
                        type: 'line',
                        data: totalData,
                        smooth: true,
                        lineStyle: { color: '#FFFFFF', width: 3 },
                        itemStyle: { color: '#FFFFFF' },
                        showSymbol: false,
                        animationDuration: 100,
                        z: 10
                    });
                    
                    chartInstance.current.setOption({
                        series: series
                    }, { replaceMerge: ['series'] });

                    // Publish the freshly computed data to the export handlers.
                    bandsRef.current = bands;
                    totalDataRef.current = totalData;

                    // Setup Graphic elements for dragging (export lives in the HTML toolbar).
                    setTimeout(() => {
                        if (!chartInstance.current) return;

                        const graphics = bands.map((b, i) => {
                            const pos = chartInstance.current.convertToPixel({seriesIndex: 0}, [b.freq, b.type === 'peaking' ? b.gain : 0]);
                            if (!pos) return null;
                            const bandColor = getBandColor(b.name);
                            return {
                                type: 'circle',
                                id: `band_handle_${i}`,
                                position: pos,
                                shape: { r: 12 },
                                style: { fill: bandColor, stroke: '#fff', lineWidth: 2, shadowBlur: 4, shadowColor: '#000' },
                                invisible: false,
                                draggable: true,
                                z: 100,
                                ondrag: function (e) {
                                    const pt = chartInstance.current.convertFromPixel({seriesIndex: 0}, [this.x, this.y]);
                                    
                                    const domainLimits = {
                                        'LoCut': { min: 20, max: 400 },
                                        'Low': { min: 25, max: 400 },
                                        'LowMid': { min: 100, max: 1600 },
                                        'Mid': { min: 400, max: 6400 },
                                        'HighMid': { min: 800, max: 12800 },
                                        'High': { min: 1600, max: 20000 },
                                        'HiCut': { min: 5000, max: 20000 }
                                    };
                                    const limit = domainLimits[b.name] || { min: 20, max: 20000 };
                                    
                                    let newFreq = Math.max(limit.min, Math.min(limit.max, pt[0]));
                                    let newGain = b.type === 'peaking' ? Math.max(-32, Math.min(32, pt[1])) : b.gain;
                                    
                                    // Update graph smoothly temporarily? The state update will do it.
                                        if (publishFn) {
                                            const topic = config?.topics ? config.topics[b.name] : `OpenAir/Gui/${config?.command}/${b.name}`;
                                            publishFn(topic, { value: newFreq, rotValue: newGain });
                                        }
                                },
                                onmousewheel: function (e) {
                                    // Q adjustment
                                    e.event.preventDefault();
                                    e.event.stopPropagation();
                                    const delta = e.event.wheelDelta || -e.event.detail;
                                    let newQ = b.q + (delta > 0 ? 0.1 : -0.1);
                                    newQ = Math.max(0.1, Math.min(10.0, newQ));
                                    if (publishFn) {
                                        const topic = config?.topics ? config.topics[b.name] : `OpenAir/Gui/${config?.command}/${b.name}`;
                                        publishFn(topic + '/Q', { value: newQ });
                                    }
                                }
                            };
                        }).filter(Boolean);

                        chartInstance.current.setOption({ graphic: graphics });
                    }, 50); // Give eCharts time to render
                }
        } catch (e) {
            console.error(e);
        }
    }, [messages, config?.command, mqttData]);

    const ctrlLabel = { display: 'flex', flexDirection: 'column', fontSize: '9px', color: '#334', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.5px' };
    const ctrlSelect = { fontSize: '11px', padding: '2px 4px', border: '1px solid #889', borderRadius: '3px', background: '#e8eef1', color: '#223', marginTop: '2px' };
    const ctrlBtn = { fontSize: '11px', fontWeight: 'bold', padding: '5px 12px', border: '1px solid #556', borderRadius: '4px', background: '#334', color: '#fff', cursor: 'pointer', alignSelf: 'flex-end' };

    return (
        <div style={{ width: '100%', padding: '2px', backgroundColor: '#bbcad1', borderRadius: '4px', border: '1px solid #778', boxSizing: 'border-box' }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-end', gap: '8px', padding: '4px 6px' }}>
                <label style={ctrlLabel}>
                    Taps
                    <select style={ctrlSelect} value={firTaps} onChange={(e) => setFirTaps(parseInt(e.target.value, 10))}>
                        {[512, 1024, 2048, 4096, 8192, 16384].map(n => (
                            <option key={n} value={n}>{n}</option>
                        ))}
                    </select>
                </label>
                <label style={ctrlLabel}>
                    Sample Rate
                    <select style={ctrlSelect} value={firSampleRate} onChange={(e) => setFirSampleRate(parseInt(e.target.value, 10))}>
                        {[44100, 48000, 88200, 96000, 192000].map(n => (
                            <option key={n} value={n}>{n >= 1000 ? (n / 1000) + ' kHz' : n}</option>
                        ))}
                    </select>
                </label>
                <label style={ctrlLabel}>
                    Phase
                    <select style={ctrlSelect} value={firPhase} onChange={(e) => setFirPhase(e.target.value)}>
                        <option value="linear">Linear</option>
                        <option value="minimum">Minimum</option>
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
                <button style={ctrlBtn} onClick={handleExportFIR}>Export FIR</button>
                <button style={{ ...ctrlBtn, background: '#556' }} onClick={handleExportCSV}>Export CSV</button>
            </div>
            <div
                ref={chartRef}
                style={{ width: '100%', height, position: 'relative' }}
            />
        </div>
    );
};

window.Equalization = Equalization;
 
