/**
 * Header: Equalization.jsx
 * Purpose: Equalization component or utility.
 * Description: Handles logic and rendering for Equalization component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// Equalization Graph Component
// Renders a specialized frequency equalization curve based on ECharts.

// Inline comment: Logic for Equalization
const Equalization = ({ value: mqttData, config, topic }) => {
    const chartRef = React.useRef(null);
    const chartInstance = React.useRef(null);
    const useMqttLang = window.useMqttLang || (() => ['En', () => {}]);
    const [lang] = useMqttLang();

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
                min: 20,
                max: 20000,
                axisLabel: {
                    formatter: function (value) {
                        if (value === 20) return '20';
                        if (value === 200) return '200';
                        if (value === 2000) return '2k';
                        if (value === 20000) return '20k';
                        return '';
                    },
                    color: '#f48a20',
                    fontWeight: 'bold'
                },
                splitLine: { show: false },
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
                splitLine: { show: false },
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

    // Handle real-time MQTT updates
    React.useEffect(() => {
        if (!chartInstance.current) return;
        try {
            const bands = [];
            const baseTopic = `OpenAir/Gui/${config?.command}`;

            const unwrap = (v) => {
                if (v === undefined || v === null) return undefined;
                if (typeof v === 'object' && v.value !== undefined) return v.value;
                return v;
            };

            const parseBand = (key, bandData, ltpParsed, gainParsed) => {
                let freq = unwrap(bandData?.Freq) ?? unwrap(bandData?.freq) ?? unwrap(bandData?.Frequency) ?? unwrap(bandData?.frequency);
                let gain = unwrap(bandData?.Gain) ?? unwrap(bandData?.gain);
                let q = unwrap(bandData?.Q) ?? unwrap(bandData?.q);
                
                if (freq === undefined && ltpParsed) freq = ltpParsed.value;
                if (q === undefined && ltpParsed) q = ltpParsed.rotValue;
                if (gain === undefined && gainParsed) gain = gainParsed.value !== undefined ? gainParsed.value : gainParsed;
                
                freq = parseFloat(freq);
                gain = parseFloat(gain);
                q = parseFloat(q) || 1.0;
                
                if (!isNaN(freq) && !isNaN(gain) && !isNaN(q)) {
                    bands.push({ name: key, freq, gain, q });
                }
            };

            // 1. Scrape the raw messages dictionary for any sub-topics matching the base topic
            const bandKeys = ['Low', 'LowMid', 'Mid', 'HighMid', 'High'];
            bandKeys.forEach(key => {
                const ltpMsg = messages[`${baseTopic}/${key}`];
                const gainMsg = messages[`${baseTopic}/${key}/Gain`];
                let ltpParsed = null;
                let gainParsed = null;
                
                if (ltpMsg) {
                    try { ltpParsed = JSON.parse(ltpMsg); } catch(e) {}
                }
                if (gainMsg) {
                    try { gainParsed = JSON.parse(gainMsg); } catch(e) {}
                }
                
                if (ltpParsed || gainParsed) {
                    parseBand(key, {}, ltpParsed, gainParsed);
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
            if (bands.length > 0) {
                    const steps = 500; // Using 500 points to match the user's Excel precision
                    const minF = Math.log10(20);
                    const maxF = Math.log10(20000);
                    
                    const totalData = [];
                    const bandDataArray = bands.map(() => []);
                    
                    const fs = 48000;
                    
                    const getBiquadGainDB = (f, fc, Q, gainDB) => {
                        if (gainDB === 0) return 0;
                        const A = Math.pow(10, gainDB / 40);
                        const w0 = 2 * Math.PI * fc / fs;
                        const alpha = Math.sin(w0) / (2 * Q);

                        const b0 = 1 + alpha * A;
                        const b1 = -2 * Math.cos(w0);
                        const b2 = 1 - alpha * A;
                        const a0 = 1 + alpha / A;
                        const a1 = -2 * Math.cos(w0);
                        const a2 = 1 - alpha / A;

                        const M0 = b0 / a0;
                        const M1 = b1 / a0;
                        const M2 = b2 / a0;
                        const P1 = a1 / a0;
                        const P2 = a2 / a0;

                        const w = 2 * Math.PI * f / fs;
                        const cos_w = Math.cos(w);
                        const cos_2w = Math.cos(2 * w);

                        const num = M0*M0 + M1*M1 + M2*M2 + 2*(M0*M1 + M1*M2)*cos_w + 2*M0*M2*cos_2w;
                        const den = 1 + P1*P1 + P2*P2 + 2*(P1 + P1*P2)*cos_w + 2*P2*cos_2w;

                        return 10 * Math.log10(num / den);
                    };
                    
                    for (let i = 0; i <= steps; i++) {
                        const f = Math.pow(10, minF + (maxF - minF) * (i / steps));
                        let totalGain = 0;
                        
                        bands.forEach((b, bIdx) => {
                            const bandGain = getBiquadGainDB(f, b.freq, b.q, b.gain);
                            totalGain += bandGain;
                            bandDataArray[bIdx].push([parseFloat(f.toFixed(1)), parseFloat(bandGain.toFixed(2))]);
                        });
                        
                        totalData.push([parseFloat(f.toFixed(1)), parseFloat(totalGain.toFixed(2))]);
                    }
                    
                    const bandColors = ['#FF5722', '#4CAF50', '#03A9F4', '#E91E63', '#9C27B0', '#FFEB3B'];
                    
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
                        series.push({
                            name: b.name || `Band ${i+1}`,
                            type: 'line',
                            data: bandDataArray[i],
                            smooth: true,
                            lineStyle: { color: bandColors[i % bandColors.length], width: 1 },
                            itemStyle: { color: bandColors[i % bandColors.length] },
                            areaStyle: {
                                color: bandColors[i % bandColors.length],
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

                    // Setup Graphic elements for dragging & export
                    setTimeout(() => {
                        if (!chartInstance.current) return;
                        
                        const exportFIR = () => {
                            const N = 1024;
                            const fs = 48000;
                            const H = new Float32Array(N);
                            
                            for (let k = 0; k <= N/2; k++) {
                                const f = (k * fs) / N;
                                let totalGainDB = 0;
                                if (f > 0) {
                                    bands.forEach(b => {
                                        if (b.gain !== 0) {
                                            const w = f / b.freq;
                                            const denom = 1 + (b.q * b.q) * Math.pow(w - 1/w, 2);
                                            totalGainDB += b.gain / denom;
                                        }
                                    });
                                }
                                const amp = Math.pow(10, totalGainDB / 20);
                                H[k] = amp;
                                if (k > 0 && k < N/2) H[N - k] = amp;
                            }

                            const ir = new Float32Array(N);
                            for (let n = 0; n < N; n++) {
                                let sum = 0;
                                for (let k = 0; k < N; k++) {
                                    sum += H[k] * Math.cos(2 * Math.PI * k * n / N);
                                }
                                // Shift by N/2
                                const shiftedN = (n - N/2 + N) % N;
                                // Apply Hamming window
                                const windowGain = 0.54 - 0.46 * Math.cos(2 * Math.PI * n / (N - 1));
                                ir[n] = (sum / N) * windowGain;
                            }

                            // Create WAV file
                            const buffer = new ArrayBuffer(44 + ir.length * 2);
                            const view = new DataView(buffer);
                            
                            const writeString = (offset, string) => {
                                for (let i = 0; i < string.length; i++) {
                                    view.setUint8(offset + i, string.charCodeAt(i));
                                }
                            };

                            writeString(0, 'RIFF');
                            view.setUint32(4, 36 + ir.length * 2, true);
                            writeString(8, 'WAVE');
                            writeString(12, 'fmt ');
                            view.setUint32(16, 16, true);
                            view.setUint16(20, 1, true); // PCM
                            view.setUint16(22, 1, true); // 1 channel
                            view.setUint32(24, fs, true);
                            view.setUint32(28, fs * 2, true);
                            view.setUint16(32, 2, true);
                            view.setUint16(34, 16, true);
                            writeString(36, 'data');
                            view.setUint32(40, ir.length * 2, true);

                            // Normalize and convert to 16-bit
                            let maxVal = 0;
                            for (let i = 0; i < ir.length; i++) maxVal = Math.max(maxVal, Math.abs(ir[i]));
                            if (maxVal === 0) maxVal = 1;
                            
                            for (let i = 0; i < ir.length; i++) {
                                let s = Math.max(-1, Math.min(1, ir[i] / maxVal));
                                view.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
                            }

                            const blob = new Blob([view], { type: 'audio/wav' });
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = 'eq_fir_filter.wav';
                            a.click();
                            URL.revokeObjectURL(url);
                        };

                        const graphics = bands.map((b, i) => {
                            const pos = chartInstance.current.convertToPixel({seriesIndex: 0}, [b.freq, b.gain]);
                            return {
                                type: 'circle',
                                id: `band_handle_${i}`,
                                position: pos,
                                shape: { r: 12 },
                                style: { fill: bandColors[i % bandColors.length], stroke: '#fff', lineWidth: 2, shadowBlur: 4, shadowColor: '#000' },
                                invisible: false,
                                draggable: true,
                                z: 100,
                                ondrag: function (e) {
                                    const pt = chartInstance.current.convertFromPixel({seriesIndex: 0}, this.position);
                                    let newFreq = Math.max(20, Math.min(20000, pt[0]));
                                    let newGain = Math.max(-32, Math.min(32, pt[1]));
                                    
                                    // Update graph smoothly temporarily? The state update will do it.
                                        if (window.useMqttPublish) {
                                            const publish = window.useMqttPublish();
                                            publish(topic + '/' + b.name + '/Freq', newFreq);
                                            publish(topic + '/' + b.name + '/Gain', newGain);
                                            // Vertical LTP mapping
                                            publish(topic + '/' + b.name + '/rotValue', newFreq);
                                            publish(topic + '/' + b.name + '/value', newGain);
                                        }
                                },
                                onmousewheel: function (e) {
                                    // Q adjustment
                                    e.event.preventDefault();
                                    e.event.stopPropagation();
                                    const delta = e.event.wheelDelta || -e.event.detail;
                                    let newQ = b.q + (delta > 0 ? 0.1 : -0.1);
                                    newQ = Math.max(0.1, Math.min(10.0, newQ));
                                    if (window.useMqttPublish) {
                                        const publish = window.useMqttPublish();
                                        publish(topic + '/' + b.name + '/Q', newQ);
                                    }
                                }
                            };
                        });
                        
                        graphics.push({
                            type: 'group',
                            id: 'btn_export',
                            right: 20,
                            top: 20,
                            children: [
                                {
                                    type: 'rect',
                                    z: 100,
                                    shape: { width: 90, height: 30, r: 4 },
                                    style: { fill: '#333', stroke: '#888', lineWidth: 1 }
                                },
                                {
                                    type: 'text',
                                    z: 100,
                                    style: { text: 'Export FIR', fill: '#fff', x: 14, y: 14, font: '12px sans-serif', fontWeight: 'bold' }
                                }
                            ],
                            onclick: function () {
                                exportFIR();
                            }
                        });

                        chartInstance.current.setOption({ graphic: graphics });
                    }, 50); // Give eCharts time to render
                }
        } catch (e) {
            console.error(e);
        }
    }, [messages, config?.command, mqttData]);

    return (
        <div style={{ padding: '2px', backgroundColor: '#bbcad1', borderRadius: '4px', border: '1px solid #778' }}>
            <div 
                ref={chartRef}
                style={{ width, height, position: 'relative' }}
            />
        </div>
    );
};

window.Equalization = Equalization;
