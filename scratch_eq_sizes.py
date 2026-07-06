import json
from collections import OrderedDict

with open('FrontEnd/Gui_Frames/5_Samples/6_EQ/EQ.json', 'r') as f:
    data = json.load(f, object_pairs_hook=OrderedDict)

band_controls = data['Zoo_Metering_EQ']['blocks']['Parametric_EQ_Demo']['fields']['Band_Controls']

for band_id, band in band_controls['fields'].items():
    if 'LTP_Freq_Gain' in band['fields']:
        ltp = band['fields']['LTP_Freq_Gain']
        if 'layout' in ltp:
            ltp['layout']['height'] = 40
            
    if 'Q_Knob' in band['fields']:
        q = band['fields']['Q_Knob']
        # Add layout to Q_Knob
        q['layout'] = {
            "width": 90,
            "height": 90
        }

with open('FrontEnd/Gui_Frames/5_Samples/6_EQ/EQ.json', 'w') as f:
    json.dump(data, f, indent=2)

