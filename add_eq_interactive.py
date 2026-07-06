import re
import os

jsx_file = "/home/anthony/Documents/OPEN-AIR/FrontEnd/libControl/graphing/Equalization/Equalization.jsx"

with open(jsx_file, "r") as f:
    jsx_code = f.read()

# Replace the React.useEffect that handles mqttData
old_effect_pattern = re.compile(r"    // Handle real-time MQTT updates\s+React\.useEffect\(\(\) => \{.*?\}, \[mqttData\]\);", re.DOTALL)

new_effect = """    // Handle real-time MQTT updates
    React.useEffect(() => {
        if (!mqttData || !chartInstance.current) return;
        try {
            if (typeof mqttData === 'string' && mqttData.includes(',')) {
                const newData = parseCsv("x,y\\n" + mqttData);
                if (newData.length) {
                    chartInstance.current.setOption({
                        series: [{ data: [[20,0],[20000,0]] }, { data: newData }]
                    });
                }
            } else if (typeof mqttData === 'object') {
                const bands = [];
                for (const key in mqttData) {
                    const band = mqttData[key];
                    if (band && typeof band === 'object') {
                        const freq = parseFloat(band.Freq || band.freq || band.Frequency || band.frequency);
                        const gain = parseFloat(band.Gain || band.gain);
                        const q = parseFloat(band.Q || band.q);
                        if (!isNaN(freq) && !isNaN(gain) && !isNaN(q)) {
                            bands.push({ name: key, freq, gain, q });
                        }
                    }
                }
                
                if (bands.length > 0) {
                    const steps = 200;
                    const minF = Math.log10(20);
                    const maxF = Math.log10(20000);
                    
                    const totalData = [];
                    const bandDataArray = bands.map(() => []);
                    
                    for (let i = 0; i <= steps; i++) {
                        const f = Math.pow(10, minF + (maxF - minF) * (i / steps));
                        let totalGain = 0;
                        
                        bands.forEach((b, bIdx) => {
                            let bandGain = 0;
                            if (b.gain !== 0) {
                                const w = f / b.freq;
                                const denom = 1 + (b.q * b.q) * Math.pow(w - 1/w, 2);
                                bandGain = b.gain / denom;
                                totalGain += bandGain;
                            }
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
            }
        } catch (e) {
            console.error(e);
        }
    }, [mqttData, topic]);"""

jsx_code = old_effect_pattern.sub(new_effect, jsx_code)

with open(jsx_file, "w") as f:
    f.write(jsx_code)

print("Equalization.jsx updated with graphic drag elements and FIR generator.")
