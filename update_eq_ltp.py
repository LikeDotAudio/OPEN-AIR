import json

file_path = "/home/anthony/Documents/OPEN-AIR/FrontEnd/Gui_Frames/5_Samples/2_Metering/6_EQ/EQ.json"

with open(file_path, "r") as f:
    data = json.load(f)

bands_data = [
    {"name": "Low", "color": "#FF5722", "f_def": 60.0, "g_def": 2.5, "q_def": 0.7},
    {"name": "LowMid", "color": "#4CAF50", "f_def": 250.0, "g_def": -4.0, "q_def": 1.2},
    {"name": "Mid", "color": "#03A9F4", "f_def": 1000.0, "g_def": 1.5, "q_def": 2.0},
    {"name": "HighMid", "color": "#E91E63", "f_def": 4000.0, "g_def": 0.0, "q_def": 1.5},
    {"name": "High", "color": "#9C27B0", "f_def": 12000.0, "g_def": 3.0, "q_def": 0.7}
]

# Fix graph geometry to avoid the tiny vertical sliver issue with "100%"
eq_graph = data["Zoo_Metering_EQ"]["blocks"]["Parametric_EQ_Demo"]["fields"]["EQ_Graph"]
eq_graph["geometry"]["width"] = 1000
eq_graph["geometry"]["height"] = 400

band_controls = data["Zoo_Metering_EQ"]["blocks"]["Parametric_EQ_Demo"]["fields"]["Band_Controls"]["fields"]

for i, b in enumerate(bands_data):
    band_id = f"Band_{i}"
    # Replace the Freq and Gain with an LTP, keep Q
    band_controls[band_id]["layout_columns"] = 2
    band_controls[band_id]["column_sizing"] = [{"weight": 3}, {"weight": 1}]
    
    band_controls[band_id]["fields"] = {
        "LTP_Freq_Gain": {
            "type": "_CustomLTP",
            "command": f"EQ_Params/{b['name']}",
            "label": { "En": "Gain / Freq" },
            "fader_config": {
                "domain": { "min": -24.0, "max": 24.0 },  # Gain is linear value
                "value": { "default_value": b["g_def"] },
                "cosmetics": { "colors": { "highlight": b["color"] } },
                "readout": { "show_value": False, "show_units": False }
            },
            "knob_config": {
                "rotation_min": 20.0,
                "rotation_max": 20000.0,
                "rotation_default": b["f_def"],  # Freq is rotary value
                "cap_outline_color": b["color"],
                "freestyle": True
            },
            "layout": {
                "width": 80,
                "height": 300
            }
        },
        f"Q_{i}": {
            "type": "_FaderKnob",
            "command": f"EQ_Params/{b['name']}/Q",
            "label": { "En": "Q" },
            "domain": { "primary": { "min": 0.1, "max": 10.0, "value_default": b["q_def"] } },
            "cosmetics": { "colors": { "pointer": b["color"] } },
            "layout": { "width": "100%", "height": 300 }
        }
    }

with open(file_path, "w") as f:
    json.dump(data, f, indent=2)

print("EQ.json updated with vertical LTPFaders.")
