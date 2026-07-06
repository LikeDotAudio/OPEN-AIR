import json

file_path = '/home/anthony/Documents/OPEN-AIR/FrontEnd/Gui_Frames/5_Samples/2_Metering/2_Bar_Meter/0_REF/reference_meters_bargraphs.json'

with open(file_path, 'r') as f:
    data = json.load(f)

blocks = data['Zoo_Metering_Bar_Meter_REF']['blocks']
new_blocks = {}
spacer_index = 1

for i, (key, block) in enumerate(blocks.items()):
    new_blocks[key] = block
    
    # Don't add a spacer after the very last block
    if i < len(blocks) - 1:
        spacer_key = f"SpacerBlock_{spacer_index}"
        new_blocks[spacer_key] = {
            "type": "OcaBlock",
            "layout_columns": 1,
            "column_sizing": [{"weight": 1}],
            "fields": {
                f"SpacerField_{spacer_index}": {
                    "type": "Spacer",
                    "geometry": {
                        "width": "100%",
                        "height": 40
                    }
                }
            }
        }
        spacer_index += 1

data['Zoo_Metering_Bar_Meter_REF']['blocks'] = new_blocks

with open(file_path, 'w') as f:
    json.dump(data, f, indent=2)

print("Spacers inserted successfully.")
