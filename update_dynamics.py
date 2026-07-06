import json

file_path = "/home/anthony/Documents/OPEN-AIR/FrontEnd/Gui_Frames/5_Samples/2_Metering/7_Dynamics/Dynamics.json"

with open(file_path, "r") as f:
    data = json.load(f)

# Update graph block
graph_block = data["Zoo_Metering_Dynamics"]["blocks"]["Dynamics_Demo"]["fields"]["graph"]
graph_block["command"] = "Dyn_Params"
graph_block["geometry"] = {"width": 800, "height": 400}

# Add Controls block
data["Zoo_Metering_Dynamics"]["blocks"]["Dyn_Controls"] = {
    "type": "OcaBlock",
    "description": { "En": "Dynamics Controls" },
    "layout_columns": 6,
    "fields": {
        "Thresh": {
            "type": "_FaderKnob",
            "command": "Dyn_Params/Thresh",
            "label": { "En": "Thresh" },
            "domain": { "primary": { "min": -60.0, "max": 0.0, "value_default": -20.0 } },
            "layout": { "height": 200 }
        },
        "Ratio": {
            "type": "_FaderKnob",
            "command": "Dyn_Params/Ratio",
            "label": { "En": "Ratio" },
            "domain": { "primary": { "min": 1.0, "max": 20.0, "value_default": 2.0 } },
            "layout": { "height": 200 }
        },
        "Knee": {
            "type": "_FaderKnob",
            "command": "Dyn_Params/Knee",
            "label": { "En": "Knee" },
            "domain": { "primary": { "min": 0.0, "max": 30.0, "value_default": 5.0 } },
            "layout": { "height": 200 }
        },
        "Gain": {
            "type": "_FaderKnob",
            "command": "Dyn_Params/Gain",
            "label": { "En": "Gain" },
            "domain": { "primary": { "min": -24.0, "max": 24.0, "value_default": 0.0 } },
            "layout": { "height": 200 }
        },
        "Attack": {
            "type": "_FaderKnob",
            "command": "Dyn_Params/Attack",
            "label": { "En": "Attack" },
            "domain": { "primary": { "min": 0.1, "max": 100.0, "value_default": 10.0 } },
            "layout": { "height": 200 }
        },
        "Release": {
            "type": "_FaderKnob",
            "command": "Dyn_Params/Release",
            "label": { "En": "Release" },
            "domain": { "primary": { "min": 10.0, "max": 1000.0, "value_default": 100.0 } },
            "layout": { "height": 200 }
        }
    }
}

with open(file_path, "w") as f:
    json.dump(data, f, indent=2)

print("Updated Dynamics.json")
