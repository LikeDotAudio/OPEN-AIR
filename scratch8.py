import json
from collections import OrderedDict

with open('FrontEnd/Gui_Frames/5_Samples/6_EQ/EQ.json', 'r') as f:
    data = json.load(f, object_pairs_hook=OrderedDict)

band_controls = data['Zoo_Metering_EQ']['blocks']['Parametric_EQ_Demo']['fields']['Band_Controls']

# Reorder the bands: Parametrics first, then Cuts
fields = band_controls['fields']
new_fields = OrderedDict()
for key in ['Band_0', 'Band_1', 'Band_2', 'Band_3', 'Band_4', 'LoCut_Band', 'HiCut_Band']:
    if key in fields:
        new_fields[key] = fields[key]

band_controls['fields'] = new_fields
band_controls['layout_columns'] = 5

if 'column_sizing' in band_controls:
    del band_controls['column_sizing']

color_map = {
    'Band_0': '#4CAF50', # Green
    'Band_1': '#FFEB3B', # Yellow
    'Band_2': '#FFEB3B', # Yellow
    'Band_3': '#FFEB3B', # Yellow
    'Band_4': '#F44336', # Red
    # Keeping existing colors for cuts
}

for band_id, band in band_controls['fields'].items():
    color = color_map.get(band_id)
    
    # Setup LTP
    if 'LTP_Freq_Gain' in band['fields']:
        ltp = band['fields']['LTP_Freq_Gain']
        if 'knob_config' not in ltp:
            ltp['knob_config'] = {}
        ltp['knob_config']['knob_style'] = 'wbs-elma'
        
        if color:
            ltp['knob_config']['cap_color'] = color
            ltp['knob_config']['cap_outline_color'] = color
            
            # update highlight color in fader_config
            if 'fader_config' in ltp and 'cosmetics' in ltp['fader_config'] and 'colors' in ltp['fader_config']['cosmetics']:
                ltp['fader_config']['cosmetics']['colors']['highlight'] = color

    # Setup Q_Knob
    if 'Q_Knob' in band['fields']:
        q = band['fields']['Q_Knob']
        if 'cosmetics' not in q:
            q['cosmetics'] = {}
        q['cosmetics']['knob_style'] = 'wbs-elma'
        if color:
            if 'colors' not in q['cosmetics']:
                q['cosmetics']['colors'] = {}
            q['cosmetics']['colors']['pointer'] = color
            q['cosmetics']['colors']['cap_color'] = color

with open('FrontEnd/Gui_Frames/5_Samples/6_EQ/EQ.json', 'w') as f:
    json.dump(data, f, indent=2)
