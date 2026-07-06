import json

with open('FrontEnd/Gui_Frames/5_Samples/6_EQ/EQ.json', 'r') as f:
    data = json.load(f)

blocks = data['Zoo_Metering_EQ']['blocks']['Parametric_EQ_Demo']['fields']['Band_Controls']['fields']

domains = {
    'Band_LoCut': {'min': 20.0, 'max': 400.0},
    'Band_0': {'min': 25.0, 'max': 400.0},
    'Band_1': {'min': 100.0, 'max': 1600.0},
    'Band_2': {'min': 400.0, 'max': 6400.0},
    'Band_3': {'min': 800.0, 'max': 12800.0},
    'Band_4': {'min': 1600.0, 'max': 20000.0},
    'Band_HiCut': {'min': 5000.0, 'max': 20000.0}
}

for band_id, domain in domains.items():
    if band_id in blocks and 'LTP_Freq_Gain' in blocks[band_id]['fields']:
        blocks[band_id]['fields']['LTP_Freq_Gain']['fader_config']['domain'] = domain

with open('FrontEnd/Gui_Frames/5_Samples/6_EQ/EQ.json', 'w') as f:
    json.dump(data, f, indent=2)

