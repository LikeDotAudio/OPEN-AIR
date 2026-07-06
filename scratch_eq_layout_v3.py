import json
from collections import OrderedDict

with open('FrontEnd/Gui_Frames/5_Samples/6_EQ/EQ.json', 'r') as f:
    data = json.load(f, object_pairs_hook=OrderedDict)

band_controls = data['Zoo_Metering_EQ']['blocks']['Parametric_EQ_Demo']['fields']['Band_Controls']['fields']

# Re-order the fields in Band_Controls to have Spacers in row 2
new_band_controls = OrderedDict()

# Row 1
for b in ['Band_0', 'Band_1', 'Band_2', 'Band_3', 'Band_4']:
    if b in band_controls:
        # Add a break line inside each band between LTP and lower controls
        band = band_controls[b]
        band_fields = band.get('fields', OrderedDict())
        
        new_fields = OrderedDict()
        for k, v in band_fields.items():
            new_fields[k] = v
            if k == 'LTP_Freq_Gain':
                # Insert a spacer block here
                new_fields['LTP_Break'] = {
                    "type": "_Label",
                    "label": {"En": ""},
                    "layout": {"width": "100%", "height": 30}
                }
        band['fields'] = new_fields
        new_band_controls[b] = band

# Row 2
if 'Band_LoCut' in band_controls:
    new_band_controls['Band_LoCut'] = band_controls['Band_LoCut']

# 3 Spacers
new_band_controls['Spacer_1'] = {"type": "_Label", "label": {"En": ""}}
new_band_controls['Spacer_2'] = {"type": "_Label", "label": {"En": ""}}
new_band_controls['Spacer_3'] = {"type": "_Label", "label": {"En": ""}}

if 'Band_HiCut' in band_controls:
    new_band_controls['Band_HiCut'] = band_controls['Band_HiCut']

data['Zoo_Metering_EQ']['blocks']['Parametric_EQ_Demo']['fields']['Band_Controls']['fields'] = new_band_controls

with open('FrontEnd/Gui_Frames/5_Samples/6_EQ/EQ.json', 'w') as f:
    json.dump(data, f, indent=2)

