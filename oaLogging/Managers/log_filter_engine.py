
import inspect

from oaLogging.Methods.matrix_gate import matrix_log

# Managers/log_filter_engine.py
# Author: Gemini CLI
# Version: 20260315.150000.REV01
#
# Description: Dynamic Runtime Log Filtering Engine for OPEN-AIR.

"""
Dynamic Runtime Log Filtering Engine.

Purpose:
    Allows for runtime adjustment of log levels via MQTT commands,
    enabling dynamic control over log verbosity without application restarts.

Responsibilities:
    - Subscribe to MQTT topic 'OPEN-AIR/system/logger/filter/set'.
    - Parse incoming JSON payloads to determine module-specific log levels.
    - Dynamically update Loguru logger filters or levels based on received rules.
    - Maintain a cache of active filters for efficient application.

Dependencies:
    - oaLogging.logger: For accessing Loguru instance and configuration.
    - workers.mqtt.mqtt_subscriber_router: For MQTT subscription.
    - json: For parsing MQTT payloads.
"""

import json

from loguru import logger

from ..Core.logger import get_logger  # Assuming logger module is accessible

# We need to import the MQTT router to subscribe to topics.
# Assuming it's structured like this, adjust if needed.
try:
    from oaComProtocols.oaComMQTT.Managers.mqtt_subscriber_router import MqttSubscriberRouter
except ImportError:
    logger.error("MqttSubscriberRouter not found. Dynamic log filtering will not function.")
    MqttSubscriberRouter = None # Placeholder to prevent further errors

from oaComProtocols.oaComMQTT.Core.mqtt_message import MqttMessage

# Global instance to manage filters and the MQTT router
_log_filter_engine = None

class LogFilterEngine:
    """Manages dynamic log filtering via MQTT."""

    def __init__(self, mqtt_router, base_logger_configurator):
        """
        Initializes the LogFilterEngine.

        Args:
            mqtt_router (MqttSubscriberRouter): The MQTT router instance.
            base_logger_configurator: A callable that reconfigures Loguru sinks.
                                      (e.g., the main initialize_logging function or a dedicated reconfiguration part).
        """
        self.mqtt_router = mqtt_router
        self.base_logger_configurator = base_logger_configurator # This might need to be more granular if sinks can be reconfigured individually.
        self.active_filters = {} # Stores current dynamic filters {module_path: level_str}
        self.logger = get_logger("LOG_FILTER") # Logger for this engine itself

        if not self.mqtt_router:
            self.logger.warning("MqttSubscriberRouter is not available. Dynamic log filtering is disabled.")
            return

        self.topic = "OPEN-AIR/system/logger/filter/set"
        self.logger.info(f"Setting up MQTT subscription for dynamic log filtering on topic: {self.topic}")
        self.mqtt_router.subscribe_to_topic(self.topic, self.handle_filter_update)

    def handle_filter_update(self, message: MqttMessage):
        """
        Handles incoming MQTT messages for log filter updates.

        Args:
            message (MqttMessage): The standardized MQTT message container.
        """
        try:
            filter_rules = message.get_json_payload()
            self.logger.debug(f"Received log filter update: {filter_rules}")

            # Validate and update filters
            new_filters = {}
            for module, level in filter_rules.items():
                if isinstance(level, str) and level.upper() in ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "OFF"]:
                    new_filters[module] = level.upper()
                else:
                    self.logger.warning(f"Invalid log level '{level}' for module '{module}'. Ignoring.")

            self.active_filters.update(new_filters) # Apply new filters, potentially overwriting existing ones

            # Reapply filters to Loguru sinks.
            # This is a crucial part and might require reconfiguring sinks.
            # For simplicity, we'll assume a way to update Loguru's internal filters.
            # A more robust approach might involve removing and re-adding sinks with new filters.
            self._apply_filters_to_loguru()
            self.logger.info(f"Log filters updated. Current filters: {self.active_filters}")

        except json.JSONDecodeError:
            self.logger.error(f"Failed to decode JSON payload for log filter update: {payload}")
        except Exception as e:
            self.logger.error(f"Error handling log filter update: {e}")

    def _apply_filters_to_loguru(self):
        """
        Applies the current active_filters to Loguru sinks.

        This is a placeholder and requires specific knowledge of how Loguru sinks
        are managed and reconfigured. A common approach is to remove existing sinks
        and add them back with updated filter configurations.
        """
        # This is a complex operation and depends heavily on how sinks are managed.
        # For now, we'll log that it *should* happen.
        self.logger.info("Attempting to apply dynamic filters to Loguru sinks. (Implementation pending)")

        # Example of how one might *conceptually* do this if sinks were managed centrally:
        # logger.remove() # Remove all existing sinks
        # self.base_logger_configurator() # Re-initialize with base settings (e.g., console, file)
        #     # Add sinks with specific filters for the module
        #     # This requires a more sophisticated logger setup function
        #     pass

        # A simpler approach might be to modify filters on existing sinks if Loguru allows it.
        # If not, re-adding sinks is necessary. The current logger.py does not expose sink management well.
        # We will need to ensure the `initialize_logging` function is aware of this engine.

def initialize_filter_engine(mqtt_router, logger_reconfigurator_callable):
    """
    Initializes and starts the LogFilterEngine if MQTT is available.

    Args:
        mqtt_router (MqttSubscriberRouter): The MQTT router instance.
        logger_reconfigurator_callable: A callable that can reconfigure Loguru sinks.
                                        This is passed so the engine can re-apply filters.
    """
    global _log_filter_engine
    if MqttSubscriberRouter and mqtt_router:
        _log_filter_engine = LogFilterEngine(mqtt_router, logger_reconfigurator_callable)
        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "LogFilterEngine initialized and subscribed to MQTT topic.", "INFO")
    else:
        logger.warning("LogFilterEngine could not be initialized: MQTT router unavailable.")

# --- Mock/Placeholder for demonstration if MqttSubscriberRouter is not available ---
class MockMqttSubscriberRouter:
    def __init__(self):
        self.logger = get_logger("MOCK_MQTT")
        self.logger.warning("Using Mock MQTT Router. MQTT subscriptions will not work.")

    def subscribe_to_topic(self, topic_filter, callback_func):
        self.logger.info(f"Mock MQTT: Subscribing to {topic_filter} (no-op)")

# --- Example of how to use this module ---
if __name__ == "__main__":
    # This is a standalone example. In the actual application,
    # initialize_filter_engine would be called after the MQTT router
    # and logger are initialized.

    # Mock logger initialization
    from oaLogging.Core.logger import get_logger as mock_get_logger
    from oaLogging.Core.logger import initialize_logging as mock_init_logging

    class MockConfig: # Dummy config for testing
        global_settings = {"debug_enabled": True}

    mock_log_dir = "./mock_logs"
    mock_init_logging(MockConfig(), log_dir=mock_log_dir, partition="TEST")

    # Mock logger instance
    mock_logger_for_engine = mock_get_logger("ENGINE_TEST")
    mock_logger_for_engine.info("Logger initialized for engine test.")

    # Mock MQTT router and pass it to the engine initializer
    mock_mqtt_router = MockMqttSubscriberRouter()

    # The reconfigurator callable needs to be defined or passed correctly.
    # For simplicity here, we'll just pass the initialisation function,
    # assuming it can be called again to reconfigure sinks.
    def mock_reconfigure_sinks():
        mock_logger_for_engine.info("Simulating sink reconfiguration...")
        # In a real scenario, this would remove and re-add sinks with new filters.
        pass

    initialize_filter_engine(mock_mqtt_router, mock_reconfigure_sinks)

    mock_logger_for_engine.info("LogFilterEngine setup complete.")

    # Simulate receiving a filter update
    if _log_filter_engine:
        mock_logger_for_engine.info("Simulating MQTT message...")
        test_payload = '{"Manager.Display": "WARNING", "Worker.Logic": "TRACE"}'
        mock_message = MqttMessage(topic="OPEN-AIR/system/logger/filter/set", payload=test_payload)
        _log_filter_engine.handle_filter_update(mock_message)

    # Add a message that should be filtered out by the simulated rules
    mock_logger_for_engine.trace("This is a trace message for Worker.Logic (should be filtered out by simulated rule)")
    mock_logger_for_engine.warning("This is a warning message for Manager.Display (should be kept)")

    print("Log filtering simulation finished. Check mock_logs/ for output if configured.")
    print("NOTE: This is a mock execution. Actual MQTT communication and sink reconfiguration")
    print("      would occur in a live environment.")
