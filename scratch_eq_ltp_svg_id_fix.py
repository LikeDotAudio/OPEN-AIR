import re

with open('FrontEnd/libControl/faders/LTPFader/LTPFader.jsx', 'r') as f:
    code = f.read()

old_elma = """                        <window.KnobCapWBSElma 
                            center={capRadius}
                            radius={capRadius}
                            angle={-(((currentRotVal - rotMin) / ((rotMax - rotMin) || 200)) * 2 - 1) * 135}
                            config={{"""

new_elma = """                        <window.KnobCapWBSElma 
                            filterId={`ltpfader-${topic.replace(/\\W/g, '_')}`}
                            center={capRadius}
                            radius={capRadius}
                            angle={-(((currentRotVal - rotMin) / ((rotMax - rotMin) || 200)) * 2 - 1) * 135}
                            config={{"""

if old_elma in code:
    code = code.replace(old_elma, new_elma)
    with open('FrontEnd/libControl/faders/LTPFader/LTPFader.jsx', 'w') as f:
        f.write(code)
    print("Successfully added filterId to WBSElma inside LTPFader!")
else:
    print("Failed to find old elma block!")
