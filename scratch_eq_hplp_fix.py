import re

with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'r') as f:
    code = f.read()

old_logic = """                let enabled = type !== 'peaking' ? (gain > 0) : (gain !== 0);

                if (!isNaN(freq) && !isNaN(gain) && !isNaN(q)) {
                    bands.push({ name: key, freq, gain, q, type, enabled });
                }"""

new_logic = """                // Filters like HP/LP often don't have a gain parameter
                if (type === 'highpass' || type === 'lowpass') {
                    if (isNaN(gain)) gain = 0;
                }
                
                let enabled = false;
                if (type === 'highpass') enabled = freq > 20.5; // Enable if slightly above 20Hz
                else if (type === 'lowpass') enabled = freq < 19999; // Enable if slightly below 20kHz
                else enabled = gain !== 0;

                if (!isNaN(freq) && !isNaN(gain) && !isNaN(q)) {
                    bands.push({ name: key, freq, gain, q, type, enabled });
                }"""

if old_logic in code:
    code = code.replace(old_logic, new_logic)
    with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'w') as f:
        f.write(code)
    print("Successfully patched parseBand HP/LP logic!")
else:
    print("Could not find the old logic!")
