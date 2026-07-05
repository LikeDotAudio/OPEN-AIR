# ==========================================
# Header: update_crafty_zoo.py
# Purpose: update_crafty_zoo.py implementation.
# Description: Logic and implementation for update_crafty_zoo.py implementation.
# 
# Version: 26.07.05.1
# Change Log:
# - 2026-07-05: Initial annotation and documentation added.
# ==========================================

import os
import json
import re

readme_path = "/home/anthony/Documents/OPEN-AIR/FrontEnd/libControl/Knobs/Knob/Readme.md"
with open(readme_path, "r") as f:
    content = f.read()

match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
if match:
    json_str = match.group(1)
    data = json.loads(json_str)
    
    # We will let the user use the WYSIWYG to pick "spoked_pan", "spoked_spread", etc., but we don't necessarily need to add 4 new examples to the Grab Bag.
    # However, to be safe we can add them to the _LEGEND if it exists, or just create Zoo entries.
    # Wait, there's no _LEGEND for variants in the Readme currently, the `variant` was just added in cosmetics.
    pass

# Update the Zoo file for Crafty Knobs
zoo_path = "/home/anthony/Documents/OPEN-AIR/FrontEnd/Gui_Frames/Window_2/right_50/top_100/9_Zoo/2_Knobs/3_Crafty/Crafty.json"
if os.path.exists(zoo_path):
    with open(zoo_path, "r") as f:
        zoo_data = json.load(f)
    
    blocks = zoo_data.get("Zoo_Knobs_Crafty", {}).get("blocks", {}).get("Crafty_Knobs_Demo", {})
    if "fields" in blocks:
        # Update layout columns to 5 to fit the new knobs
        blocks["layout_columns"] = 5
        
        # Add the new knobs
        blocks["fields"]["knob_spoked_pan"] = {
            "type": "_SmartKnob",
            "label": { "En": "Pan (Spoked)", "show_label": True },
            "domain": { "primary": { "min": -100, "max": 100, "value_default": 0, "step": 1 } },
            "geometry": { "width": 100, "height": 100 },
            "cosmetics": { "visualization": "crafty", "variant": "spoked_pan", "colors": { "primary": "#9370db", "secondary": "#5a3d7c" } }
        }
        
        blocks["fields"]["knob_spoked_spread"] = {
            "type": "_SmartKnob",
            "label": { "En": "Spread (Spoked)", "show_label": True },
            "geometry": { "width": 100, "height": 100 },
            "cosmetics": { "visualization": "crafty", "variant": "spoked_spread", "colors": { "primary": "#f4d03f", "secondary": "#5a3d7c" } }
        }

        blocks["fields"]["knob_led_pan"] = {
            "type": "_SmartKnob",
            "label": { "En": "Pan (LED)", "show_label": True },
            "domain": { "primary": { "min": -100, "max": 100, "value_default": 0, "step": 1 } },
            "geometry": { "width": 100, "height": 100 },
            "cosmetics": { "visualization": "crafty", "variant": "led_ring_pan", "colors": { "primary": "#33A1FD", "secondary": "#444" } }
        }
        
        blocks["fields"]["knob_led_spread"] = {
            "type": "_SmartKnob",
            "label": { "En": "Spread (LED)", "show_label": True },
            "geometry": { "width": 100, "height": 100 },
            "cosmetics": { "visualization": "crafty", "variant": "led_ring_spread", "colors": { "primary": "#ff4d4d", "secondary": "#444" } }
        }

    with open(zoo_path, "w") as f:
        json.dump(zoo_data, f, indent=2)
    print("Updated Zoo file with new Crafty variants.")
