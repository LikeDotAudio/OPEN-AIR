import re

with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'r') as f:
    code = f.read()

code = code.replace('const unwrap = (v) =>', 'const unwrapMqtt = (v) =>')
code = code.replace('unwrap(', 'unwrapMqtt(')

with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'w') as f:
    f.write(code)

print("Renamed unwrap to unwrapMqtt to prevent naming collisions!")
