# managers/yak/yak_trigger_handler.py
#
# Handles the monitoring and distribution of "Yak" related MQTT messages to the GUI.
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

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config
from workers.Command_Router.mqtt.mqtt_message import MqttMessage

app_constants = Config.get_instance()

# Global list of callbacks (observers)
_gui_observers = []

def register_monitor_callback(callback_func):
    """
    Registers a GUI callback function to receive Yak traffic.
    """
    if callback_func not in _gui_observers:
        _gui_observers.append(callback_func)
        if LOCAL_DEBUG: logger.success("✅ Yak Monitor GUI registered.")

def unregister_monitor_callback(callback_func):
    """
    Unregisters a GUI callback.
    """
    if callback_func in _gui_observers:
        _gui_observers.remove(callback_func)

def handle_yak_monitor_traffic(msg: MqttMessage):
    """
    Called by the MQTT Router when a message containing 'yak' is detected.
    Distributes the message to registered GUI observers.
    """
    topic = msg.topic
    payload = msg.decode_payload()
    
    # Notify all registered GUIs
    for callback in _gui_observers:
        try:
            callback(topic, payload)
        except Exception as e:
             if LOCAL_DEBUG:
                 logger.exception("❌ Error updating Yak Monitor GUI")
