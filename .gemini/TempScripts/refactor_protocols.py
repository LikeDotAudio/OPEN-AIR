import os
import shutil
import configparser

base_dir = "/home/anthony/Documents/OPEN-AIR/oaComProtocols"
legacy_dir = os.path.join(base_dir, ".legacy_python")

if not os.path.exists(legacy_dir):
    os.makedirs(legacy_dir)

protocols = [
    "AES70", "DNSSD", "Ember", "MDNS", "Midi", "MQTT",
    "Nmos", "OSC", "REST", "SAP", "SMPTE2138", "SNMP", "Visa", "Websocket"
]

for p in protocols:
    folder_name = f"oaCom{p}"
    folder_path = os.path.join(base_dir, folder_name)
    
    # Move to legacy if it exists
    if os.path.exists(folder_path):
        dest_path = os.path.join(legacy_dir, folder_name)
        if not os.path.exists(dest_path):
            shutil.move(folder_path, legacy_dir)
            
    # Create the config INI file
    config = configparser.ConfigParser()
    config[p] = {
        "enabled": "true",
        "port": "8080",  # Placeholder
        "mqtt_listen_topics": f"OpenAir/{p}/Inbound/#",
        "mqtt_push_topics": f"OpenAir/{p}/Outbound/#",
        "mqtt_ignore_topics": f"OpenAir/{p}/Ignore/#"
    }
    
    ini_path = os.path.join(base_dir, f"config{p}.ini")
    with open(ini_path, "w") as configfile:
        config.write(configfile)

print("Protocols refactored successfully.")
