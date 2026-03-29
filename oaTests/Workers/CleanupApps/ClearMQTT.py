# oaTests/Workers/CleanupApps/ClearMQTT.py
# Author: Anthony Peter Kuzub
# Version: 20260323.2030.1
#
# Description: Standalone maintenance script to wipe the OPEN-AIR MQTT topic tree.

import socket
import time
import sys
import argparse
import logging
import paho.mqtt.client as mqtt

LOCAL_DEBUG = True    # Set to False in production, True for dev on this file

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("MQTTSweeper")

def check_mqtt_port(host, port, timeout=1.0):
    """Verifies the MQTT broker port is reachable without using exceptions."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

class MQTTSweeper:
    def __init__(self, host, port, base_topic):
        self.host = host
        self.port = port
        self.base_topic = base_topic
        self.topics = set()
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        
    def on_message(self, client, userdata, message):
        # ⚡ PRECONDITION VALIDATION: Ensure message and topic are valid
        if not message or not hasattr(message, 'topic'):
            return
            
        topic = message.topic
        # Only track if it's actually under our base topic
        if topic and topic.startswith(self.base_topic):
            self.topics.add(topic)

    def sweep(self):
        """Discovers and deletes all topics (including retained) under the configured base topic."""
        if LOCAL_DEBUG: logger.info(f"📡📤📤 [CLEAR_MQTT] Starting MQTT Deep Sweep on {self.host}:{self.port} (Root: {self.base_topic})...")
        
        # ⚡ PRECONDITION VALIDATION: Verify port is open before connect()
        if not check_mqtt_port(self.host, self.port):
            logger.error(f"❌ Connection failed: Port {self.port} on {self.host} is unreachable.")
            return

        self.client.on_message = self.on_message
        
        # We assume host and port are validated. 
        # connect() will only be called if the port check passed.
        self.client.connect(self.host, self.port, 60)

        # Subscribe to catch existing retained messages
        wildcard = f"{self.base_topic}/#"
        # Subscribe to both root and wildcard to be thorough
        self.client.subscribe([(self.base_topic, 0), (wildcard, 0)])
        
        # 1. Discovery Phase
        if LOCAL_DEBUG: logger.info(f"  └─ 🕵️ Discovery: Scanning for active/retained topics under {self.base_topic}...")
        self.client.loop_start()
        
        # Wait for retained messages to arrive. 
        # 2 seconds is usually enough for a local broker to dump retained state.
        time.sleep(2.0) 
        
        self.client.loop_stop()
        
        if not self.topics:
            if LOCAL_DEBUG: logger.info(f"✨ No topics found under {self.base_topic}. Broker is already clean.")
            self.client.disconnect()
            return

        if LOCAL_DEBUG: logger.info(f"  └─ 📋 Found {len(self.topics)} topics to clear.")

        # 2. Deletion Phase
        self.client.loop_start() # Restart loop to handle PUBACKs
        
        count = 0
        publish_handles = []
        
        # Sort reverse to potentially delete children before parents
        for topic in sorted(list(self.topics), reverse=True):
            # To delete a retained topic, publish a zero-length payload with retain=True
            logger.info(f"  Deleting MQTT topic: {topic}") # Log each topic being cleared
            msg_info = self.client.publish(topic, payload=None, qos=1, retain=True)
            publish_handles.append(msg_info)
            count += 1
            if count % 100 == 0:
                if LOCAL_DEBUG: logger.info(f"    ├─ Sent clear command for {count} topics...")
        
        # Wait for all deletion messages to be acknowledged by the broker
        if LOCAL_DEBUG: logger.info("  └─ ⏳ Finalizing: Waiting for broker acknowledgments...")
        for handle in publish_handles:
            # wait_for_publish can still raise if the loop is not running or other state issues.
            # but we assume the loop is running and we are within timeout.
            # Using a polling check instead of a blocking call with exception
            start_wait = time.time()
            while not handle.is_published() and (time.time() - start_wait) < 1.0:
                time.sleep(0.01)
        
        self.client.loop_stop()
        if LOCAL_DEBUG: logger.info(f"✨ Successfully wiped {count} topics (and cleared retained state) from {self.base_topic} tree.")
        self.client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Standalone MQTT Topic Tree Sweeper")
    parser.add_argument("--host", type=str, default="localhost", help="MQTT Broker Host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT Broker Port")
    parser.add_argument("--topic", type=str, default="OPEN-AIR", help="Base Topic to Sweep")
    
    args = parser.parse_args()
    
    sweeper = MQTTSweeper(args.host, args.port, args.topic)
    sweeper.sweep()
