# oaTranslator/Managers/yak_trigger_handler.py
#
# Distributes YAK traffic and monitor events to registered GUI observers.
# Implements the Observer pattern for decoupled UI updates.
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
# Version 20260406.1940.1

import inspect

from loguru import logger

from oaComProtocols.oaComMQTT.Core.mqtt_message import MqttMessage
from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()

# --- Internal Registry ---
# Global list of callbacks (observers) representing UI dashboard instances.
_gui_observers = []

def register_monitor_callback(callback_func):
    """
    Registers a GUI callback function to receive real-time YAK traffic.

    Args:
        callback_func (callable): Function accepting (topic, payload) strings.

    Side Effects:
        - Appends the function to the global '_gui_observers' list.
        - Logs the registration event to the matrix gate.
    """
    if callback_func not in _gui_observers:
        _gui_observers.append(callback_func)
        matrix_log("UI", "TRANSLATOR", inspect.currentframe().f_code.co_name,
                   "✅ [CONFIG] Yak Monitor GUI registered.", level="SUCCESS")

def unregister_monitor_callback(callback_func):
    """
    Removes a GUI callback from the active notification list.

    Args:
        callback_func (callable): The previously registered callback.
    """
    if callback_func in _gui_observers:
        _gui_observers.remove(callback_func)

def handle_yak_monitor_traffic(message: MqttMessage):
    """
    Dispatches filtered MQTT traffic to all registered UI observers.

    Typically invoked by the MQTT Router when traffic matching 'yak/monitor/#' 
    is detected. Ensures that the UI Partition's diagnostic dashboards are 
    kept in sync with background translation events.

    Args:
        message (MqttMessage): The incoming message containing topic and payload.

    Warn:
        - Callbacks are executed sequentially; long-running callbacks will 
          block the router thread.
    """
    topic = message.topic
    payload = message.decode_payload()

    # Notify all registered GUI dashboards.
    for callback in _gui_observers:
        try:
            callback(topic, payload)
        except Exception:
             logger.exception("❌ [UI] Error updating Yak Monitor dashboard.")
