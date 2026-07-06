import json
import os

file1 = "/home/anthony/Documents/OPEN-AIR/FrontEnd/Gui_Frames/5_Samples/0_Faders/1_Vertical/3_Variety/Experimental.json"
file2 = "/home/anthony/Documents/OPEN-AIR/FrontEnd/Gui_Frames/5_Samples/0_Faders/1_Vertical/4_More Variety/Experimental.json"

with open(file1, "r") as f:
    data = json.load(f)

# The root key is "Zoo_Faders_Vertical_Experimental"
root_key = "Zoo_Faders_Vertical_Experimental"
block_key = "Experimental_Fader_Riot"

original_block = data[root_key]["blocks"][block_key]
fields = original_block["fields"]
columns = original_block["column_sizing"]

# First 10
data1 = json.loads(json.dumps(data)) # Deep copy
b1 = data1[root_key]["blocks"][block_key]
b1["layout_columns"] = 10
b1["column_sizing"] = columns[:10]
b1["fields"] = {k: fields[k] for i, k in enumerate(fields) if i < 10}
b1["description"]["En"] = "10 Columns of Experimental Fader Madness (Part 1)"

with open(file1, "w") as f:
    json.dump(data1, f, indent=2)

# Next 10
data2 = json.loads(json.dumps(data))
b2 = data2[root_key]["blocks"][block_key]
b2["layout_columns"] = 10
b2["column_sizing"] = columns[10:]
b2["fields"] = {k: fields[k] for i, k in enumerate(fields) if i >= 10}
b2["description"]["En"] = "10 Columns of Experimental Fader Madness (Part 2)"

with open(file2, "w") as f:
    json.dump(data2, f, indent=2)

print("Split completed successfully!")
