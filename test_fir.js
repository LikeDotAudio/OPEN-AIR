const bands = [
  { freq: 20, q: 0.7, gain: 1, type: 'highpass', enabled: true },
  { freq: 100, q: 1, gain: 0, type: 'peaking', enabled: false }
];

const fs = 48000;
const getBiquadGainDB = (f, fc, Q, gainDB, type = 'peaking', enabled = true) => {
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

const exportFIR = () => {
    const N = 1024;
    const fs = 48000;
    const H = new Float32Array(N);
    
    for (let k = 0; k <= N/2; k++) {
        const f = (k * fs) / N;
        let totalGainDB = 0;
        if (f > 0) {
            bands.forEach(b => {
                totalGainDB += getBiquadGainDB(f, b.freq, b.q, b.gain, b.type, b.enabled);
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

    // Create .FIR plain text file (one coefficient per line)
    let firContent = "";
    for (let i = 0; i < ir.length; i++) {
        firContent += ir[i].toFixed(10) + "\n";
    }
    console.log("Success! len =", firContent.length);
};

exportFIR();
