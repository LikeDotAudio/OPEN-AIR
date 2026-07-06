import json

with open('FrontEnd/Gui_Frames/5_Samples/2_Metering/6_EQ/EQ.json', 'r') as f:
    data = json.load(f)

bands = data["Zoo_Metering_EQ"]["blocks"]["Parametric_EQ_Demo"]["fields"]["Band_Controls"]["fields"]
band_keys = ["Band_0", "Band_1", "Band_2", "Band_3", "Band_4"]

for b in band_keys:
    block = bands[b]
    block["layout_columns"] = 1
    if "column_sizing" in block:
        del block["column_sizing"]
    
    fields = block["fields"]
    new_fields = {}
    topic_base = ""
    for k, v in fields.items():
        if v["type"] == "_CustomLTP":
            topic_base = v["topic"]
            v["label"]["En"] = "Freq / Gain"
            v["knob_config"]["rotation_min"] = -32.0
            v["knob_config"]["rotation_max"] = 32.0
            v["knob_config"]["rotation_default"] = 0.0
            v["knob_config"]["freestyle"] = True
            v["fader_config"]["domain"]["min"] = 20.0
            v["fader_config"]["domain"]["max"] = 20000.0
            new_fields["LTP_Freq_Gain"] = v
            break

    # Add the Q knob
    new_fields["Q_Knob"] = {
        "type": "_Knob",
        "label": { "En": "Q" },
        "domain": {
            "primary": { "min": 0.1, "max": 10.0, "value_default": 0.7 }
        },
        "cosmetics": {
            "colors": {
                "pointer": "#4CAF50" # Just default, will inherit or customize if needed
            }
        },
        "layout": { "width": "100%", "height": 80 },
        "topic": topic_base + "/Q"
    }

    block["fields"] = new_fields

with open('FrontEnd/Gui_Frames/5_Samples/2_Metering/6_EQ/EQ.json', 'w') as f:
    json.dump(data, f, indent=2)

