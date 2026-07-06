import re

with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'r') as f:
    code = f.read()

# 1. Fix Shelf Parsing
old_parse = """                // Shelf overrides
                if (key.toLowerCase() === 'low' && String(messages[`OpenAir/Gui/EQ_Params/Low/Shelf`]) === '1') {
                    type = 'lowshelf';
                }
                if (key.toLowerCase() === 'high' && String(messages[`OpenAir/Gui/EQ_Params/High/Shelf`]) === '1') {
                    type = 'highshelf';
                }"""

new_parse = """                const getParsedMsg = (t) => {
                    if (!messages[t]) return null;
                    try { return JSON.parse(messages[t]); } catch(e) { return messages[t]; }
                };
                const lowShelf = unwrap(getParsedMsg('OpenAir/Gui/EQ_Params/Low/Shelf'));
                const highShelf = unwrap(getParsedMsg('OpenAir/Gui/EQ_Params/High/Shelf'));
                
                // Shelf overrides
                if (key.toLowerCase() === 'low' && (lowShelf == 1 || lowShelf === true)) {
                    type = 'lowshelf';
                }
                if (key.toLowerCase() === 'high' && (highShelf == 1 || highShelf === true)) {
                    type = 'highshelf';
                }"""

code = code.replace(old_parse, new_parse)

# 2. Fix 1st order shelf math
old_shelf_math = """                        } else if (type === 'lowshelf') {
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

new_shelf_math = """                        } else if (type === 'lowshelf') {
                            if (gainDB === 0) return 0;
                            const V = Math.pow(10, Math.abs(gainDB) / 20);
                            const K = Math.tan(w0 / 2);
                            if (gainDB > 0) {
                                // Boost
                                b0 = 1 + V * K;
                                b1 = V * K - 1;
                                b2 = 0;
                                a0 = 1 + K;
                                a1 = K - 1;
                                a2 = 0;
                            } else {
                                // Cut
                                b0 = 1 + K;
                                b1 = K - 1;
                                b2 = 0;
                                a0 = 1 + V * K;
                                a1 = V * K - 1;
                                a2 = 0;
                            }
                        } else if (type === 'highshelf') {
                            if (gainDB === 0) return 0;
                            const V = Math.pow(10, Math.abs(gainDB) / 20);
                            const K = Math.tan(w0 / 2);
                            if (gainDB > 0) {
                                // Boost
                                b0 = V + K;
                                b1 = K - V;
                                b2 = 0;
                                a0 = 1 + K;
                                a1 = K - 1;
                                a2 = 0;
                            } else {
                                // Cut
                                b0 = 1 + K;
                                b1 = K - 1;
                                b2 = 0;
                                a0 = V + K;
                                a1 = K - V;
                                a2 = 0;
                            }
                        } else {"""

code = code.replace(old_shelf_math, new_shelf_math)

# 3. Fix FIR Export (Export CSV FIR doesn't work)
old_export = """    const exportData = () => {
        // Find existing logic or inject it
    }"""
# Wait, let's see what export button does. I'll search for 'Export CSV FIR' in the file.
