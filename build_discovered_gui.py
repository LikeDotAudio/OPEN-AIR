import paho.mqtt.client as mqtt
import json
import os
import time

GUI_FRAMES_DIR = "/home/anthony/Documents/OPEN-AIR/FrontEnd/Gui_Frames/0_discovered"

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("visa/Device/#")

def on_message(client, userdata, msg):
    topic = msg.topic
    # Example: visa/Device/DMM/34401A/DC Voltage/value
    parts = topic.split('/')
    if len(parts) < 4:
        return
    
    category = parts[2]
    model = parts[3]
    
    # Create the base directory for this category and model
    base_dir = os.path.join(GUI_FRAMES_DIR, category, model)
    os.makedirs(base_dir, exist_ok=True)
    
    # We create a simple JSON file for the category if it doesn't exist
    category_file = os.path.join(GUI_FRAMES_DIR, category, f"{category}.json")
    if not os.path.exists(category_file):
        config = {
            category: {
                "type": "OcaBin",
                "description": {"En": f"Discovered {category} Devices"},
                "blocks": {
                    model: {
                        "type": "OcaBlock",
                        "label": {"active": {"text": {"En": model}}},
                        "fields": {}
                    }
                }
            }
        }
        with open(category_file, 'w') as f:
            json.dump(config, f, indent=2)

    # For sub-elements, let's create a basic readout block if it ends in 'value'
    if parts[-1] == "value":
        sub_element = parts[-2]
        field_name = sub_element.replace(" ", "_")
        
        # We can append it to the category file or create a separate file
        sub_file = os.path.join(base_dir, f"{field_name}.json")
        if not os.path.exists(sub_file):
            config = {
                field_name: {
                    "type": "_GuiValue",
                    "label": {"En": sub_element},
                    "subscribe": topic
                }
            }
            with open(sub_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"Created GUI element for {topic} -> {sub_file}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print("Starting auto-discovery GUI builder...")
client.connect("127.0.0.1", 1883, 60)
client.loop_start()

# Let it run for 5 seconds to collect retained messages
time.sleep(5)
client.loop_stop()
print("Done collecting discovered devices.")
