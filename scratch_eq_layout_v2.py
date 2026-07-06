import json
from collections import OrderedDict

with open('FrontEnd/Gui_Frames/5_Samples/6_EQ/EQ.json', 'r') as f:
    data = json.load(f, object_pairs_hook=OrderedDict)

band_controls = data['Zoo_Metering_EQ']['blocks']['Parametric_EQ_Demo']['fields']['Band_Controls']['fields']

band_colors = {
    'Band_0': '#4CAF50', # Green
    'Band_1': '#FFEB3B', # Yellow
    'Band_2': '#FFEB3B', # Yellow
    'Band_3': '#FFEB3B', # Yellow
    'Band_4': '#F44336', # Red
}

shelf_topic_map = {
    'Band_0': 'OpenAir/Gui/EQ_Params/Low/Shelf',
    'Band_4': 'OpenAir/Gui/EQ_Params/High/Shelf'
}

for band_id, color in band_colors.items():
    band = band_controls[band_id]
    fields = band.get('fields', {})
    
    # 1. Update LTP
    ltp = fields.get('LTP_Freq_Gain')
    if ltp:
        ltp['layout'] = {"width": "100%", "height": 100}
        
        if 'knob_config' not in ltp:
            ltp['knob_config'] = {}
        ltp['knob_config']['cap_color'] = color
        
        if color == '#FFEB3B':
            if 'cosmetics' not in ltp:
                ltp['cosmetics'] = {}
            if 'line' not in ltp['cosmetics']:
                ltp['cosmetics']['line'] = {}
            ltp['cosmetics']['line']['color'] = '#000000'

    # Extract Q_Knob and Shelf_Switch
    q_knob = fields.pop('Q_Knob', None)
    shelf = fields.pop('Shelf_Switch', None)
    
    # Check if they are inside Lower_Controls already
    if 'Lower_Controls' in fields:
        lc_fields = fields['Lower_Controls'].get('fields', {})
        if 'Q_Knob' in lc_fields:
            q_knob = lc_fields['Q_Knob']
        if 'Shelf_Switch' in lc_fields:
            shelf = lc_fields['Shelf_Switch']
            
    # Remove Lower_Controls so we can rebuild it or skip it
    fields.pop('Lower_Controls', None)

    if q_knob:
        q_knob['layout'] = {"width": 120, "height": 120}
        if color == '#FFEB3B':
            if 'cosmetics' not in q_knob:
                q_knob['cosmetics'] = {}
            if 'line' not in q_knob['cosmetics']:
                q_knob['cosmetics']['line'] = {}
            q_knob['cosmetics']['line']['color'] = '#000000'

    # 2. Rebuild layout
    if band_id in ['Band_0', 'Band_4']:
        # Needs Lower_Controls with 3 columns
        lc = OrderedDict()
        lc['type'] = 'OcaBlock'
        lc['layout_columns'] = 3
        lc['description'] = {"show_label": False}
        lc['column_sizing'] = [{"weight": 1}, {"weight": 1}, {"weight": 1}]
        lc['fields'] = OrderedDict()
        
        # Create fresh shelf switch
        new_shelf = {
            "type": "_Button",
            "label": {"En": "Shelf Mode"},
            "domain": {"primary": {"min": 0, "max": 1, "value_default": 0}},
            "layout": {"width": 60, "height": 40},
            "topic": shelf_topic_map[band_id]
        }
        
        spacer = {"type": "_Label", "label": {"En": ""}}
        
        if band_id == 'Band_0':
            # Shelf left, Q middle, spacer right
            lc['fields']['Shelf_Switch'] = new_shelf
            if q_knob: lc['fields']['Q_Knob'] = q_knob
            lc['fields']['Spacer'] = spacer
        else:
            # spacer left, Q middle, Shelf right
            lc['fields']['Spacer'] = spacer
            if q_knob: lc['fields']['Q_Knob'] = q_knob
            lc['fields']['Shelf_Switch'] = new_shelf
            
        fields['Lower_Controls'] = lc
    else:
        # Just put Q_Knob back directly
        if q_knob:
            fields['Q_Knob'] = q_knob

with open('FrontEnd/Gui_Frames/5_Samples/6_EQ/EQ.json', 'w') as f:
    json.dump(data, f, indent=2)

