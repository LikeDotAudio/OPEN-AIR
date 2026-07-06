import re

with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'r') as f:
    code = f.read()

old_biquad = """                    const getBiquadGainDB = (f, fc, Q, gainDB, type = 'peaking', enabled = true) => {
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
                        } else if (type === 'lowshelf') {
                            if (gainDB === 0) return 0;
                            const A = Math.pow(10, gainDB / 40);
                            const beta = Math.sqrt(A) / Q;
                            b0 =    A * ( (A+1) - (A-1)*Math.cos(w0) + beta*Math.sin(w0) );
                            b1 =  2*A * ( (A-1) - (A+1)*Math.cos(w0)                     );
                            b2 =    A * ( (A+1) - (A-1)*Math.cos(w0) - beta*Math.sin(w0) );
                            a0 =          (A+1) + (A-1)*Math.cos(w0) + beta*Math.sin(w0)  ;
                            a1 =   -2 * ( (A-1) + (A+1)*Math.cos(w0)                     );
                            a2 =          (A+1) + (A-1)*Math.cos(w0) - beta*Math.sin(w0)  ;
                        } else if (type === 'highshelf') {
                            if (gainDB === 0) return 0;
                            const A = Math.pow(10, gainDB / 40);
                            const beta = Math.sqrt(A) / Q;
                            b0 =    A * ( (A+1) + (A-1)*Math.cos(w0) + beta*Math.sin(w0) );
                            b1 = -2*A * ( (A-1) + (A+1)*Math.cos(w0)                     );
                            b2 =    A * ( (A+1) + (A-1)*Math.cos(w0) - beta*Math.sin(w0) );
                            a0 =          (A+1) - (A-1)*Math.cos(w0) + beta*Math.sin(w0)  ;
                            a1 =    2 * ( (A-1) - (A+1)*Math.cos(w0)                     );
                            a2 =          (A+1) - (A-1)*Math.cos(w0) - beta*Math.sin(w0)  ;
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
                    };"""

new_math = """                    const getBiquadGainDB = (f, fc, Q, gainDB, type = 'peaking', enabled = true) => {
                        if (!enabled) return 0;
                        
                        // Exact analog bode plot transfer functions for Bell/Shelf
                        if (type === 'lowshelf' || type === 'highshelf' || type === 'peaking') {
                            if (gainDB === 0) return 0;
                            const V = Math.pow(10, gainDB / 20); // Linear amplitude
                            const x = f / fc; // Normalized frequency ratio
                            let magnitudeSq = 1;

                            if (type === 'lowshelf') {
                                // First order low shelf: |H(jw)|^2 = (x^2 + V^2) / (x^2 + 1)
                                magnitudeSq = (Math.pow(x, 2) + Math.pow(V, 2)) / (Math.pow(x, 2) + 1);
                            } else if (type === 'highshelf') {
                                // First order high shelf: |H(jw)|^2 = (V^2 * x^2 + 1) / (x^2 + 1)
                                magnitudeSq = (Math.pow(V * x, 2) + 1) / (Math.pow(x, 2) + 1);
                            } else if (type === 'peaking') {
                                // Second order bell: |H(jw)|^2 = [ (1 - x^2)^2 + (V/Q * x)^2 ] / [ (1 - x^2)^2 + (1/Q * x)^2 ]
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
                    };"""

if old_biquad in code:
    code = code.replace(old_biquad, new_math)
    with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'w') as f:
        f.write(code)
    print("Successfully replaced biquad math!")
else:
    print("Could not find old biquad block!")
