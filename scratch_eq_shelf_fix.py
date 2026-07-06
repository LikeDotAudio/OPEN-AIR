import re

with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'r') as f:
    code = f.read()

old_shelf = """                // Shelf overrides
                if (key.toLowerCase() === 'low' && messages[`OpenAir/Gui/EQ_Params/Low/Shelf`] === '1') {
                    type = 'lowshelf';
                }
                if (key.toLowerCase() === 'high' && messages[`OpenAir/Gui/EQ_Params/High/Shelf`] === '1') {
                    type = 'highshelf';
                }"""

new_shelf = """                // Shelf overrides
                if (key.toLowerCase() === 'low' && String(messages[`OpenAir/Gui/EQ_Params/Low/Shelf`]) === '1') {
                    type = 'lowshelf';
                }
                if (key.toLowerCase() === 'high' && String(messages[`OpenAir/Gui/EQ_Params/High/Shelf`]) === '1') {
                    type = 'highshelf';
                }"""

code = code.replace(old_shelf, new_shelf)

with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'w') as f:
    f.write(code)

