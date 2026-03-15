# workers/Command_Router/Mqtt_Manager/Stand_Alone_Purge.py
#
# Standalone utility to purge the entire 'OPEN-AIR' MQTT topic tree.
# Connects to the broker defined in config.ini and clears all retained messages.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20260314.000000.1

import time
import sys
import os
import paho.mqtt.client as mqtt
import configparser

# --- Standard Debug Logging Setup ---
# Local simple print if loguru is not available in standalone context
def log(msg):
    print(f"🧹 [MQTT PURGE] {msg}")

def purge_mqtt():
    # 1. Read config.ini for broker settings
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'config.ini')
    
    if not os.path.exists(config_path):
        log(f"❌ Error: config.ini not found at {config_path}")
        return False

    try:
        config.read(config_path)
        broker_address = config.get('MQTT', 'broker_address', fallback='localhost')
        broker_port = config.getint('MQTT', 'broker_port', fallback=1883)
    except Exception as e:
        log(f"❌ Error reading config: {e}")
        return False

    log(f"Connecting to broker at {broker_address}:{broker_port}...")

    # 2. Setup MQTT Client
    topics_to_delete = set()
    
    def on_message(client, userdata, msg):
        topics_to_delete.add(msg.topic)

    client = mqtt.Client()
    client.on_message = on_message

    try:
        client.connect(broker_address, broker_port, 60)
    except Exception as e:
        log(f"❌ Connection failed: {e}")
        return False

    # 3. Discover all retained topics under OPEN-AIR/
    log("Scanning for retained topics under 'OPEN-AIR/#'...")
    client.subscribe("OPEN-AIR/#")
    
    # Start loop to receive messages
    client.loop_start()
    
    # Wait for discovery (timeout after 2 seconds of silence or 5 seconds total)
    start_time = time.time()
    last_count = 0
    while time.time() - start_time < 5:
        time.sleep(0.5)
        if len(topics_to_delete) > 0 and len(topics_to_delete) == last_count:
            # No new topics found in the last 0.5s
            break
        last_count = len(topics_to_delete)

    client.loop_stop()
    client.unsubscribe("OPEN-AIR/#")

    if not topics_to_delete:
        log("✅ No retained topics found. MQTT is already clean.")
        client.disconnect()
        return True

    log(f"Found {len(topics_to_delete)} topics to purge.")

    # 4. Delete topics by sending empty retained messages
    for topic in topics_to_delete:
        try:
            # log(f"Deleting: {topic}")
            client.publish(topic, payload=None, qos=1, retain=True)
        except Exception as e:
            log(f"⚠️ Failed to delete {topic}: {e}")

    log(f"✅ Successfully purged {len(topics_to_delete)} topics.")
    client.disconnect()
    return True

if __name__ == "__main__":
    purge_mqtt()
