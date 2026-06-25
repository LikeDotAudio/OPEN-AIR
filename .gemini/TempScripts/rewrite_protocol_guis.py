import os
import json
from pathlib import Path

PROTOCOLS_DIR = Path("/home/anthony/Documents/OPEN-AIR/Gui_Frames/Window_2/left_50/top_100/4_Protocals")

def create_standard_protocol_layout(protocol_name, block_id):
    topic_base = f"OpenAir/Protocol/{protocol_name}"
    
    return {
        "HostInput": {
            "type": "OcaTextInput",
            "topic": f"{topic_base}/Host",
            "label": {
                "active": {"text": {"En": "IP Address"}}
            },
            "layout": {"width": 200, "height": 30}
        },
        "PortInput": {
            "type": "OcaTextInput",
            "topic": f"{topic_base}/Port",
            "label": {
                "active": {"text": {"En": "Port"}}
            },
            "layout": {"width": 100, "height": 30}
        },
        "EnableToggle": {
            "type": "OcaCheckbox",
            "topic": f"{topic_base}/Enable",
            "label": {
                "active": {"text": {"En": "Enable Protocol"}}
            },
            "layout": {"width": 150, "height": 30}
        },
        "TrafficLog": {
            "type": "OcaListbox",
            "topic": f"{topic_base}/Log",
            "label": {
                "active": {"text": {"En": "Traffic Log"}}
            },
            "layout": {"width": 350, "height": 200}
        }
    }

def process_directory(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                file_path = Path(root) / file
                
                with open(file_path, 'r') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        continue
                        
                modified = False
                for key, root_obj in data.items():
                    if "blocks" in root_obj:
                        protocol_name = key.replace("Migrated_", "")
                        for block_key, block_obj in root_obj["blocks"].items():
                            if "fields" in block_obj:
                                # Replace the bespoke custom type with standard components
                                block_obj["fields"] = create_standard_protocol_layout(protocol_name, block_key)
                                modified = True

                if modified:
                    with open(file_path, 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f"Updated: {file_path}")

if __name__ == "__main__":
    process_directory(PROTOCOLS_DIR)
