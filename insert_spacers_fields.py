import json

def insert_spacers_in_block(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Find the root key
    root_keys = list(data.keys())
    if not root_keys:
        return
    root_key = root_keys[0]
    
    blocks = data[root_key].get('blocks', {})
    
    for block_key, block in blocks.items():
        fields = block.get('fields', {})
        new_fields = {}
        spacer_idx = 1
        
        # Keep track of fields to add spacer between
        field_keys = list(fields.keys())
        
        for i, f_key in enumerate(field_keys):
            new_fields[f_key] = fields[f_key]
            
            # Don't add a spacer after the very last field
            if i < len(field_keys) - 1:
                spacer_key = f"SpacerField_{spacer_idx}"
                new_fields[spacer_key] = {
                    "type": "Spacer",
                    "geometry": {
                        "width": "100%",
                        "height": 40
                    }
                }
                spacer_idx += 1
                
        block['fields'] = new_fields

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

file1 = '/home/anthony/Documents/OPEN-AIR/FrontEnd/Gui_Frames/5_Samples/2_Metering/2_Bar_Meter/1_Horizontal_bar/Horizontal_bar.json'
file2 = '/home/anthony/Documents/OPEN-AIR/FrontEnd/Gui_Frames/5_Samples/2_Metering/2_Bar_Meter/2_Horizontal_Tri/tri_bar.json'

insert_spacers_in_block(file1)
insert_spacers_in_block(file2)

print("Spacers inserted in both files.")
