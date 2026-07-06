import json
from collections import OrderedDict

with open('FrontEnd/Gui_Frames/5_Samples/6_EQ/EQ.json', 'r') as f:
    data = json.load(f, object_pairs_hook=OrderedDict)

band_controls = data['Zoo_Metering_EQ']['blocks']['Parametric_EQ_Demo']['fields']['Band_Controls']['fields']

# Add shelf switch to Low Band
band_0 = band_controls['Band_0']['fields']
new_band_0 = OrderedDict()
for k, v in band_0.items():
    new_band_0[k] = v
    if k == 'Q_Knob':
        new_band_0['Shelf_Switch'] = {
            "type": "_Button",
            "label": {
                "En": "Shelf Mode"
            },
            "domain": {
                "primary": {
                    "min": 0,
                    "max": 1,
                    "value_default": 0
                }
            },
            "layout": {
                "width": 60,
                "height": 40
            },
            "topic": "OpenAir/Gui/EQ_Params/Low/Shelf"
        }
band_controls['Band_0']['fields'] = new_band_0

# Add shelf switch to High Band
band_3 = band_controls['Band_3']['fields']
new_band_3 = OrderedDict()
for k, v in band_3.items():
    new_band_3[k] = v
    if k == 'Q_Knob':
        new_band_3['Shelf_Switch'] = {
            "type": "_Button",
            "label": {
                "En": "Shelf Mode"
            },
            "domain": {
                "primary": {
                    "min": 0,
                    "max": 1,
                    "value_default": 0
                }
            },
            "layout": {
                "width": 60,
                "height": 40
            },
            "topic": "OpenAir/Gui/EQ_Params/High/Shelf"
        }
band_controls['Band_3']['fields'] = new_band_3

with open('FrontEnd/Gui_Frames/5_Samples/6_EQ/EQ.json', 'w') as f:
    json.dump(data, f, indent=2)

