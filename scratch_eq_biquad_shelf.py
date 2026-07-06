import re

with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'r') as f:
    code = f.read()

# 1. Update Biquad parser to listen to the new shelf switches
old_parser = """                let type = 'peaking';
                if (key.toLowerCase().includes('locut') || key.toLowerCase().includes('hpf')) type = 'highpass';
                if (key.toLowerCase().includes('hicut') || key.toLowerCase().includes('lpf')) type = 'lowpass';"""

new_parser = """                let type = 'peaking';
                if (key.toLowerCase().includes('locut') || key.toLowerCase().includes('hpf')) type = 'highpass';
                if (key.toLowerCase().includes('hicut') || key.toLowerCase().includes('lpf')) type = 'lowpass';
                
                // Shelf overrides
                if (key.toLowerCase() === 'low' && messages[`OpenAir/Gui/EQ_Params/Low/Shelf`] === '1') {
                    type = 'lowshelf';
                }
                if (key.toLowerCase() === 'high' && messages[`OpenAir/Gui/EQ_Params/High/Shelf`] === '1') {
                    type = 'highshelf';
                }"""

code = code.replace(old_parser, new_parser)


# 2. Add Shelf Math to the biquad equation
old_biquad = """                        if (type === 'highpass') {
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
                        } else {"""

new_biquad = """                        if (type === 'highpass') {
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
                        } else {"""

code = code.replace(old_biquad, new_biquad)

with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'w') as f:
    f.write(code)

