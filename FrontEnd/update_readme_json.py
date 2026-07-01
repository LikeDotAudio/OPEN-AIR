import json
import re

with open("/home/anthony/Documents/OPEN-AIR/FrontEnd/libControl/Knobs/Knob/Readme.md", "r") as f:
    content = f.read()

# Extract the JSON block
match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
if match:
    json_str = match.group(1)
    data = json.loads(json_str)
    
    # Add new examples
    data["Crafty_Spoked"] = {
        "type": "_SmartKnob",
        "label": { "En": "Delay", "show_label": True },
        "geometry": { "width": 80, "height": 80 },
        "cosmetics": {
            "visualization": "crafty",
            "variant": "spoked",
            "colors": { "primary": "#ffffff", "secondary": "#5a3d7c" }
        }
    }
    
    data["Crafty_Metallic"] = {
        "type": "_SmartKnob",
        "label": { "En": "Phase", "show_label": True },
        "geometry": { "width": 80, "height": 80 },
        "cosmetics": {
            "visualization": "crafty",
            "variant": "metallic",
            "colors": { "primary": "#222222", "secondary": "#444444" }
        }
    }

    data["Crafty_LED_Ring"] = {
        "type": "_SmartKnob",
        "label": { "En": "Mic", "show_label": True },
        "geometry": { "width": 80, "height": 80 },
        "cosmetics": {
            "visualization": "crafty",
            "variant": "led_ring",
            "colors": { "primary": "#88e077", "secondary": "#444444" }
        }
    }
    
    # Add "crafty" to visualizations legend if present
    if "_LEGEND" in data and "visualizations" in data["_LEGEND"]:
        if "crafty" not in data["_LEGEND"]["visualizations"]:
            data["_LEGEND"]["visualizations"].append("crafty")

    new_json_str = json.dumps(data, indent=2)
    new_content = content[:match.start()] + "```json\n" + new_json_str + "\n```" + content[match.end():]
    
    with open("/home/anthony/Documents/OPEN-AIR/FrontEnd/libControl/Knobs/Knob/Readme.md", "w") as f:
        f.write(new_content)
    print("Updated Readme.md")
else:
    print("Could not find JSON block")
