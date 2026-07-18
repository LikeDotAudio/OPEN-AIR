import json
from pathlib import Path

# The target sits next to this script; derive it rather than hard-coding an
# absolute path (which pointed at a repo location that no longer exists).
path = Path(__file__).resolve().parent / "yak_router.json"
with open(path, 'r') as f:
    data = json.load(f)

# Helper function to recursively find "_GuiActuator"
def update_actuators(node, default_label="Execute"):
    if isinstance(node, dict):
        if node.get("type") == "_GuiActuator":
            # Add or update label
            if "label" not in node:
                node["label"] = {
                    "inactive": {
                        "text": {"En": default_label},
                        "text_size": 14
                    }
                }
            else:
                node["label"]["inactive"]["text_size"] = 14
                
            # Update layout
            if "layout" not in node:
                node["layout"] = {}
            node["layout"]["height"] = 44
            node["layout"]["width"] = 250
            
        for k, v in node.items():
            if k == "Close_Channels":
                update_actuators(v, "CLOSE Channels")
            elif k == "Open_Channels":
                update_actuators(v, "OPEN Channels")
            elif k == "Select_Channel":
                update_actuators(v, "SELECT Channel")
            elif k == "Query_Channel_State":
                update_actuators(v, "QUERY State")
            elif k == "Query_Slot_ID":
                update_actuators(v, "QUERY ID")
            elif k == "Reset_System":
                update_actuators(v, "RESET System")
            elif k == "Card_Reset":
                update_actuators(v, "RESET Card")
            elif k == "Clear_State":
                update_actuators(v, "CLEAR State")
            else:
                update_actuators(v, default_label)
    elif isinstance(node, list):
        for item in node:
            update_actuators(item, default_label)

update_actuators(data)

with open(path, 'w') as f:
    json.dump(data, f, indent=2)

print("Updated yak_router.json successfully!")
