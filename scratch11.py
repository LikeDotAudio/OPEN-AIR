import json
from collections import OrderedDict

with open('FrontEnd/Gui_Frames/5_Samples/6_EQ/EQ.json', 'r') as f:
    data = json.load(f, object_pairs_hook=OrderedDict)

band_controls = data['Zoo_Metering_EQ']['blocks']['Parametric_EQ_Demo']['fields']['Band_Controls']

for band_id, band in band_controls['fields'].items():
    if 'Q_Knob' in band['fields']:
        q = band['fields']['Q_Knob']
        color = q.get('cosmetics', {}).get('colors', {}).get('cap_color')
        
        if color:
            # Overwrite cosmetics with WILD_03
            q['cosmetics'] = {
              "visualization": "wbs-elma",
              "colors": {
                "primary": "#546E7A",
                "cap": color,
                "tick": "#aaaaaa"
              },
              "styling": {
                "fill_color": "#546E7A",
                "cap_color": color,
                "outline_color": "#000",
                "outline_thickness": 1
              },
              "flutes": 18,
              "cap": {
                "show": True,
                "color": color
              },
              "wing": {
                "show": False,
                "color": "#546E7A",
                "length": 0.2,
                "both": False
              },
              "pointer_tip": {
                "show": True,
                "color": "#546E7A",
                "length": 0.2
              },
              "line": {
                "color": "#ffffff"
              },
              "scale": {
                "show": True,
                "style": "numeric",
                "count": 5,
                "length": 8,
                "thickness": 1
              }
            }

with open('FrontEnd/Gui_Frames/5_Samples/6_EQ/EQ.json', 'w') as f:
    json.dump(data, f, indent=2)
