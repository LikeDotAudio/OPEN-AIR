import re

with open('FrontEnd/libControl/faders/LTPFader/LTPFader.jsx', 'r') as f:
    code = f.read()

old_angle = "                            angle={-(((currentRotVal - rotMin) / ((rotMax - rotMin) || 200)) * 2 - 1) * 135}"
new_angle = "                            angle={-(((currentRotVal - rotMin) / ((rotMax - rotMin) || 200)) * 2 - 1) * 135 + 90}"

if old_angle in code:
    code = code.replace(old_angle, new_angle)
    with open('FrontEnd/libControl/faders/LTPFader/LTPFader.jsx', 'w') as f:
        f.write(code)
    print("Successfully added +90 to LTPFader angle!")
else:
    print("Could not find the angle calculation in LTPFader!")
