# Managers/yak_trigger_handler.py
# Author: Anthony Peter Kuzub
# Version: 20260124.000000.1
#
# Description: managers/yak/yak_trigger_handler.py

from oaLogging.Core.logger import initialize_logging, set_log_directory
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config
from oaComMQTT.Core.mqtt_message import MqttMessage

app_constants = Config.get_instance()

# Global list of callbacks (observers)
_gui_observers = []

def register_monitor_callback(callback_func):
    """
    Registers a GUI callback function to receive Yak traffic.
    """
    if callback_func not in _gui_observers:
        _gui_observers.append(callback_func)
        matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name, "✅ Yak Monitor GUI registered.", level="SUCCESS")

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
             logger.exception("❌ Error updating Yak Monitor GUI")
