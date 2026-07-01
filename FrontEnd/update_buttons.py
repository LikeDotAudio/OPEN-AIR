import json
import glob
import os

files = glob.glob("/home/anthony/Documents/OPEN-AIR/FrontEnd/Gui_Frames/Window_1/left_50/top_100/10_Console/*/Console_*.json")

for f in files:
    with open(f, 'r') as file:
        data = json.load(file)
    
    # Locate Solo_CH_On in the fader strip.
    # The structure is usually data[<frame>]["blocks"]["fader_strip"]["fields"]["Solo_CH_On"]["fields"]
    # But it might be dynamic or array based. Let's find it recursively.
    
    def find_and_replace_buttons(obj):
        if isinstance(obj, dict):
            if "Solo_CH_On" in obj and "fields" in obj["Solo_CH_On"]:
                fields = obj["Solo_CH_On"]["fields"]
                
                # Replace solo
                if "solo" in fields:
                    fields["solo"] = {
                        "type": "_HighVisButton",
                        "geometry": { "width": 50, "height": 35, "corner_radius": 6 },
                        "cosmetics": { "shape": "rect" },
                        "style": {
                            "active": { "text_color": "#FFFFFF", "rim_color": "#FAD02C", "inner_bg_color": "#222222", "glow_intensity": 8 },
                            "inactive": { "text_color": "#FFFFFF", "rim_color": "#555555", "inner_bg_color": "#111111", "glow_intensity": 0 }
                        },
                        "interaction": {
                            "options": {
                                "ON": { "label": { "active": { "text": "SOLO" } }, "selected": False },
                                "OFF": { "label": { "inactive": { "text": "SOLO" } }, "selected": True }
                            }
                        }
                    }
                
                # Replace ch_on (MUTE)
                if "ch_on" in fields:
                    fields["ch_on"] = {
                        "type": "_HighVisButton",
                        "geometry": { "width": 50, "height": 35, "corner_radius": 6 },
                        "cosmetics": { "shape": "rect" },
                        "style": {
                            "active": { "text_color": "#FF6b35", "rim_color": "#4A6EAA", "inner_bg_color": "#222222", "glow_intensity": 6 },
                            "inactive": { "text_color": "#999999", "rim_color": "#555555", "inner_bg_color": "#2a2a2a", "glow_intensity": 0 }
                        },
                        "interaction": {
                            "options": {
                                "ON": { "label": { "active": { "text": "MUTE" } }, "selected": False },
                                "OFF": { "label": { "inactive": { "text": "MUTE" } }, "selected": True }
                            }
                        }
                    }
            for k, v in obj.items():
                find_and_replace_buttons(v)
        elif isinstance(obj, list):
            for item in obj:
                find_and_replace_buttons(item)

    find_and_replace_buttons(data)
    
    with open(f, 'w') as file:
        json.dump(data, file, indent=2)

print("Updated Console tabs.")
