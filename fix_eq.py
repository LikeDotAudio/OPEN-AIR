import json

with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'r') as f:
    eq_code = f.read()

# Replace the bands.length > 0 block to always render the totalData and the buttons.
# Currently, it looks like:
#             if (bands.length > 0) {
#                     const steps = 500;
#                     const minF = Math.log10(20);

old_cond = "            if (bands.length > 0) {"
new_cond = "            if (true) {"
eq_code = eq_code.replace(old_cond, new_cond)

# Add null check for `pos`
old_pos = """                            const pos = chartInstance.current.convertToPixel({seriesIndex: 0}, [b.freq, b.gain]);
                            return {"""
new_pos = """                            const pos = chartInstance.current.convertToPixel({seriesIndex: 0}, [b.freq, b.gain]);
                            if (!pos) return null;
                            return {"""
eq_code = eq_code.replace(old_pos, new_pos)

# Add filter(Boolean) to graphics
old_graphics = """                                }
                            };
                        });"""
new_graphics = """                                }
                            };
                        }).filter(Boolean);"""
eq_code = eq_code.replace(old_graphics, new_graphics)

# Fix gain assignment where rotValue might be undefined
old_gain_assign = "                if (gain === undefined && ltpParsed) gain = ltpParsed.rotValue;"
new_gain_assign = "                if (gain === undefined && ltpParsed && ltpParsed.rotValue !== undefined) gain = ltpParsed.rotValue;"
eq_code = eq_code.replace(old_gain_assign, new_gain_assign)

with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'w') as f:
    f.write(eq_code)
