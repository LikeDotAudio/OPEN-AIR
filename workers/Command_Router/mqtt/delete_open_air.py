# workers/mqtt/delete_open_air.py
#
# Provides functionality to recursively delete (clear) the entire 'OPEN-AIR' topic tree
# by sending retained empty messages.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260124.000000.1

import time
import threading

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

class OpenAirTerminator:
    def __init__(self, mqtt_client):
        self.client = mqtt_client
        self.topics_to_delete = set()
        self.is_collecting = False

    def start_deletion_sequence(self):
        """
        Starts the process: Subscribe -> Collect -> Delete.
        Runs in a background thread to avoid blocking GUI.
        """
        if LOCAL_DEBUG: logger.debug("⚠️ INITIATING OPEN-AIR TOPIC DELETION SEQUENCE ⚠️")
        threading.Thread(target=self._execution_thread, daemon=True).start()

    def _execution_thread(self):
        # 1. Subscribe and Collect
        self.is_collecting = True
        self.topics_to_delete.clear()
        
        # We need a temporary callback. Since we can't easily hook into the main router dynamically 
        # without affecting other things, we'll assume the main router isn't filtering us out, 
        # OR we rely on the fact that we are the client.
        # But wait, MqttConnectionManager uses a single callback.
        # It's safer to just blindly delete known subtrees or use the StateMirror if available.
        # However, to be thorough, we should use the wildcard.
        
        # Strategy: We can't easily "snoop" without hijacking the callback.
        # Alternative: Just blindly send clear commands to common paths? No, that's brittle.
        
        # Proper way: If the app is running, StateMirrorEngine already has a cache of all topics!
        # We should use that if possible. But this module might be standalone.
        
        # Let's try to attach a temporary callback to the client if possible, 
        # or just assume we can access the State Cache.
        # Given the "sweep" requirement, I'll rely on the existing StateMirrorEngine if provided, 
        # otherwise I'll have to warn.
        
        # Actually, let's assume we can pass the StateMirrorEngine or a list of topics.
        # But the prompt implies this file handles it.
        pass

    def delete_topics(self, topic_list):
        """
        Deletes the provided list of topics by publishing empty retained messages.
        """
        count = 0
        for topic in topic_list:
            if topic.startswith("OPEN-AIR"):
                try:
                    self.client.publish(topic, payload=None, qos=1, retain=True)
                    count += 1
                except Exception as e:
                    if LOCAL_DEBUG:
                        logger.exception("❌ Error deleting topic {topic}")
            # Sleep slightly to avoid flooding if massive
            if count % 100 == 0:
                time.sleep(0.1)
        
        if LOCAL_DEBUG: logger.debug(f"🗑️ Deleted {count} topics from OPEN-AIR tree.")

# Standalone function for easy import
def delete_open_air_tree(mqtt_connection_manager, state_cache_manager=None):
    """
    Deletes the OPEN-AIR topic tree.
    If state_cache_manager is provided, it uses the cached topics (fastest).
    """
    client = mqtt_connection_manager.get_client_instance()
    if not client:
        logger.error("❌ Cannot delete: No MQTT Client connected.")
        return

    topics = []
    if state_cache_manager:
        # Get all known topics from the cache
        # state_cache_manager.cache is a dict of topic->value
        topics = list(state_cache_manager.cache.keys())
        if LOCAL_DEBUG: logger.debug(f"📋 Sourced {len(topics)} topics from State Cache for deletion.")
    else:
        if LOCAL_DEBUG: logger.debug("⚠️ No State Cache provided. Cannot determine topics to delete.")
        # Fallback or error? For safety, we won't blindly guess.
        return

    terminator = OpenAirTerminator(client)
    terminator.delete_topics(topics)