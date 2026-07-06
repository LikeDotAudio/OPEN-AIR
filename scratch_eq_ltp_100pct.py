import json
from collections import OrderedDict

with open('FrontEnd/Gui_Frames/5_Samples/6_EQ/EQ.json', 'r') as f:
    data = json.load(f, object_pairs_hook=OrderedDict)

def process_node(node):
    if not isinstance(node, dict):
        return
    
    if 'fields' in node:
        for k, v in node['fields'].items():
            process_node(v)
            
    if 'LTP_Freq_Gain' in node.get('fields', {}):
        ltp = node['fields']['LTP_Freq_Gain']
        if 'layout' in ltp:
            ltp['layout']['width'] = "100%"
            ltp['layout']['height'] = 70

process_node(data)

with open('FrontEnd/Gui_Frames/5_Samples/6_EQ/EQ.json', 'w') as f:
    json.dump(data, f, indent=2)

