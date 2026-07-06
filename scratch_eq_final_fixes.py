import json
from collections import OrderedDict

with open('FrontEnd/Gui_Frames/5_Samples/6_EQ/EQ.json', 'r') as f:
    data = json.load(f, object_pairs_hook=OrderedDict)

band_controls = data['Zoo_Metering_EQ']['blocks']['Parametric_EQ_Demo']['fields']['Band_Controls']['fields']

# Band_0 is Low, Band_1 is LowMid, Band_2 is Mid, Band_3 is HighMid, Band_4 is High
band_colors = {
    'Band_0': '#4CAF50', # Green
    'Band_1': '#FFEB3B', # Yellow
    'Band_2': '#FFEB3B', # Yellow
    'Band_3': '#FFEB3B', # Yellow
    'Band_4': '#F44336', # Red
}

for band_id, color in band_colors.items():
    band = band_controls[band_id]
    fields = band['fields']
    
    if 'LTP_Freq_Gain' in fields:
        ltp = fields['LTP_Freq_Gain']
        ltp['layout'] = {
            "width": "100%",
            "height": 70
        }
        
        # Ensure knob_config exists
        if 'knob_config' not in ltp:
            ltp['knob_config'] = {}
            
        ltp['knob_config']['cap_color'] = color
        
        # Set line color to black for yellow caps
        if color == '#FFEB3B':
            if 'cosmetics' not in ltp:
                ltp['cosmetics'] = {}
            if 'line' not in ltp['cosmetics']:
                ltp['cosmetics']['line'] = {}
            ltp['cosmetics']['line']['color'] = '#000000'
            
    if 'Q_Knob' in fields:
        q = fields['Q_Knob']
        q['layout'] = {
            "width": 90,
            "height": 90
        }
        
    if 'Shelf_Switch' in fields:
        # Move it to Low/High if needed, but wait! The user said "should be on the LOW and the HIGH band"
        pass

# Fix Shelf Switch placement: it should be in Band_0 (Low) and Band_4 (High)
# Remove from Band_3 if it's there
if 'Shelf_Switch' in band_controls.get('Band_3', {}).get('fields', {}):
    del band_controls['Band_3']['fields']['Shelf_Switch']

# Ensure Shelf_Switch is in Band_4
if 'Shelf_Switch' not in band_controls.get('Band_4', {}).get('fields', {}):
    band_controls['Band_4']['fields']['Shelf_Switch'] = {
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

with open('FrontEnd/Gui_Frames/5_Samples/6_EQ/EQ.json', 'w') as f:
    json.dump(data, f, indent=2)

