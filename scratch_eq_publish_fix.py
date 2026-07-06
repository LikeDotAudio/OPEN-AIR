import re

with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'r') as f:
    code = f.read()

# Add publishFn
old_publish = """    const messages = (window.useMqttMessages && window.useMqttMessages()) || {};"""

new_publish = """    const messages = (window.useMqttMessages && window.useMqttMessages()) || {};
    const publishFn = window.useMqttPublish ? window.useMqttPublish() : null;"""

code = code.replace(old_publish, new_publish)

with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'w') as f:
    f.write(code)

