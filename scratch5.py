import json

with open('FrontEnd/Gui_Frames/5_Samples/6_EQ/EQ.json', 'r') as f:
    data = json.load(f)

blocks = data['Zoo_Metering_EQ']['blocks']['Parametric_EQ_Demo']['fields']['Band_Controls']['fields']

for band_key, band in blocks.items():
    if 'LTP_Freq_Gain' in band['fields']:
        band['fields']['LTP_Freq_Gain']['wheel_controls_pot'] = True

with open('FrontEnd/Gui_Frames/5_Samples/6_EQ/EQ.json', 'w') as f:
    json.dump(data, f, indent=2)

