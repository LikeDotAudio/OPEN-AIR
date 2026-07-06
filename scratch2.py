import re

with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'r') as f:
    code = f.read()

# 1. Update parseBand
old_parse_band = """                if (!isNaN(freq) && !isNaN(gain) && !isNaN(q)) {
                    bands.push({ name: key, freq, gain, q });
                }"""
new_parse_band = """                let type = 'peaking';
                if (key.toLowerCase().includes('locut') || key.toLowerCase().includes('hpf')) type = 'highpass';
                if (key.toLowerCase().includes('hicut') || key.toLowerCase().includes('lpf')) type = 'lowpass';
                
                let enabled = type !== 'peaking' ? (gain > 0) : (gain !== 0);

                if (!isNaN(freq) && !isNaN(gain) && !isNaN(q)) {
                    bands.push({ name: key, freq, gain, q, type, enabled });
                }"""
code = code.replace(old_parse_band, new_parse_band)

# 2. Update bandKeys default
code = code.replace(
    "let bandKeys = ['Low', 'LowMid', 'Mid', 'HighMid', 'High'];",
    "let bandKeys = ['LoCut', 'Low', 'LowMid', 'Mid', 'HighMid', 'High', 'HiCut'];"
)

# 3. Update getBiquadGainDB
old_biquad = """                    const getBiquadGainDB = (f, fc, Q, gainDB) => {
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

                        const M0 = b0 / a0;"""
new_biquad = """                    const getBiquadGainDB = (f, fc, Q, gainDB, type = 'peaking', enabled = true) => {
                        if (!enabled) return 0;
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
                            if (gainDB === 0) return 0;
                            const A = Math.pow(10, gainDB / 40);
                            b0 = 1 + alpha * A;
                            b1 = -2 * Math.cos(w0);
                            b2 = 1 - alpha * A;
                            a0 = 1 + alpha / A;
                            a1 = -2 * Math.cos(w0);
                            a2 = 1 - alpha / A;
                        }

                        const M0 = b0 / a0;"""
code = code.replace(old_biquad, new_biquad)

# 4. Update the call to getBiquadGainDB
code = code.replace(
    "const bandGain = getBiquadGainDB(f, b.freq, b.q, b.gain);",
    "const bandGain = getBiquadGainDB(f, b.freq, b.q, b.gain, b.type, b.enabled);"
)

# 5. Update exportFIR to use getBiquadGainDB
old_export_inner = """                                    bands.forEach(b => {
                                        if (b.gain !== 0) {
                                            const w = f / b.freq;
                                            const denom = 1 + (b.q * b.q) * Math.pow(w - 1/w, 2);
                                            totalGainDB += b.gain / denom;
                                        }
                                    });"""
new_export_inner = """                                    bands.forEach(b => {
                                        totalGainDB += getBiquadGainDB(f, b.freq, b.q, b.gain, b.type, b.enabled);
                                    });"""
code = code.replace(old_export_inner, new_export_inner)

# 6. Update color mapping
code = code.replace(
    "'HighMid': '#E91E63',",
    "'HighMid': '#E91E63',\n                            'HiCut': '#795548',\n                            'LoCut': '#BDBDBD',"
)

# 7. Update dragging
# We want the y-axis (gain) to not snap if it's a cut filter. For cut filters, Y is always 0.
old_pos = "const pos = chartInstance.current.convertToPixel({seriesIndex: 0}, [b.freq, b.gain]);"
new_pos = "const pos = chartInstance.current.convertToPixel({seriesIndex: 0}, [b.freq, b.type === 'peaking' ? b.gain : 0]);"
code = code.replace(old_pos, new_pos)

old_new_gain = "let newGain = Math.max(-32, Math.min(32, pt[1]));"
new_new_gain = "let newGain = b.type === 'peaking' ? Math.max(-32, Math.min(32, pt[1])) : b.gain;"
code = code.replace(old_new_gain, new_new_gain)

with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'w') as f:
    f.write(code)
