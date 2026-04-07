import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# Workers/logic_mqtt_listen.py
# Author: Anthony Peter Kuzub
# Version: 20260323.1700.1
#
# Description: This manager handles listening to MQTT topics for device connection and control.

import orjson
import threading

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import VISA_LOGGER as logger
from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

# Constants for MQTT Topics
MQTT_TOPIC_SEARCH_TRIGGER = "OPEN-AIR/Device/Instrument_Connection/Search_and_Connect/Search_For_devices/trigger"
MQTT_TOPIC_DEVICE_SELECT = "OPEN-AIR/Device/Instrument_Connection/Search_and_Connect/Found_devices/options/+/selected"
MQTT_TOPIC_CONNECT_TRIGGER = (
    "OPEN-AIR/Device/Instrument_Connection/Search_and_Connect/Connect_to_Device/trigger"
)
MQTT_TOPIC_DISCONNECT_TRIGGER = (
    "OPEN-AIR/Device/Instrument_Connection/Search_and_Connect/Disconnect_device/trigger"
)
MQTT_TOPIC_CONNECT_RESOURCE_REQUEST = "OPEN-AIR/commands/instrument/connect"


class VisaMqttListener:
    """Listens for and dispatches instrument-related MQTT commands."""

    def __init__(
        self, subscriber_router, searcher, connector, disconnector, gui_publisher
    ):
        """Initializes the VisaMqttListener with required services and state."""
        self.subscriber_router = subscriber_router
        self.searcher = searcher
        self.connector = connector
        self.disconnector = disconnector
        self.gui_publisher = gui_publisher

        # ⚡ THREAD SAFETY: Protect shared mutable state
        self._state_lock = threading.Lock()
        
        self.found_resources = []
        self.selected_device_resource = None
        self.inst = None

        self._setup_mqtt_subscriptions()

    def _setup_mqtt_subscriptions(self):
        """Registers callbacks for all relevant instrument control topics."""
        try:
            self.subscriber_router.subscribe_to_topic(
                topic_filter=MQTT_TOPIC_SEARCH_TRIGGER,
                callback_func=self._on_search_request,
            )
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Subscribed to: {MQTT_TOPIC_SEARCH_TRIGGER}", "DEBUG")
            
            self.subscriber_router.subscribe_to_topic(
                topic_filter=MQTT_TOPIC_DEVICE_SELECT,
                callback_func=self._on_device_select,
            )
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Subscribed to: {MQTT_TOPIC_DEVICE_SELECT}", "DEBUG")
            
            self.subscriber_router.subscribe_to_topic(
                topic_filter=MQTT_TOPIC_CONNECT_TRIGGER,
                callback_func=self._on_gui_connect_request,
            )
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Subscribed to: {MQTT_TOPIC_CONNECT_TRIGGER}", "DEBUG")
            
            self.subscriber_router.subscribe_to_topic(
                topic_filter=MQTT_TOPIC_DISCONNECT_TRIGGER,
                callback_func=self._on_gui_disconnect_request,
            )
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Subscribed to: {MQTT_TOPIC_DISCONNECT_TRIGGER}", "DEBUG")
            
            self.subscriber_router.subscribe_to_topic(
                topic_filter=MQTT_TOPIC_CONNECT_RESOURCE_REQUEST,
                callback_func=self._on_connect_request,
            )
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Subscribed to: {MQTT_TOPIC_CONNECT_RESOURCE_REQUEST}", "DEBUG")
            
            matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "VisaMqttListener subscribed to all necessary GUI and command topics.", "SUCCESS")
        except Exception:
            logger.exception("Error in VisaMqttListener._setup_mqtt_subscriptions")

    def _on_search_request(self, topic, payload):
        """Processes a request to search for available VISA instruments."""
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Trigger received for Search Request on topic: {topic}", "DEBUG")
        try:
            if not payload:
                matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Received empty payload for Search Request on topic: {topic}. Ignoring.", "DEBUG")
                return

            payload_data = orjson.loads(payload)
            if payload_data.get("val") is True:
                matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "Processing Search for devices initiated from GUI.", "DEBUG")
                
                # Execution of search might be slow, but results must be stored safely
                found = self.searcher.search_resources()
                
                with self._state_lock:
                    self.found_resources = found
                    
                self.gui_publisher._update_found_devices_gui(found)
            else:
                matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "Ignoring Search Request, value is not 'true'.", "DEBUG")
        except (orjson.JSONDecodeError, AttributeError) as e:
            logger.error(f"Error in _on_search_request: {e}. Payload: {payload}")

    def _on_device_select(self, topic, payload):
        """Updates the selected instrument resource based on GUI selection."""
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Trigger received for Device Select on topic: {topic}", "DEBUG")
        try:
            if not payload:
                matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Received empty payload for Device Select on topic: {topic}. Ignoring.", "DEBUG")
                return

            payload_data = orjson.loads(payload)
            if payload_data.get("value") is True:
                matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "Processing Device Select, value is 'true'.", "DEBUG")
                
                # Extract the index from the topic structure: .../options/<index>/selected
                parts = topic.split("/")
                option_index = int(parts[-2]) - 1
                
                with self._state_lock:
                    if 0 <= option_index < len(self.found_resources):
                        self.selected_device_resource = self.found_resources[option_index]
                        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Device selected: {self.selected_device_resource}", "SUCCESS")
                    else:
                        self.selected_device_resource = None
            else:
                matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "Ignoring Device Select, value is not 'true'.", "DEBUG")
        except (orjson.JSONDecodeError, IndexError, ValueError, AttributeError) as e:
            logger.error(f"Error in _on_device_select: {e}. Payload: {payload}")

    def _on_gui_connect_request(self, topic, payload):
        """Initiates a connection to the selected device from the GUI."""
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Trigger received for GUI Connect Request on topic: {topic}", "DEBUG")
        try:
            if not payload:
                matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Received empty payload for GUI Connect Request on topic: {topic}. Ignoring.", "DEBUG")
                return

            payload_data = orjson.loads(payload)
            if payload_data.get("value") is True:
                matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "Processing GUI Connect Request, value is 'true'.", "DEBUG")
                
                with self._state_lock:
                    resource = self.selected_device_resource
                
                if resource:
                    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Initiating connection to {resource}...", "DEBUG")
                    # Offload to thread to prevent MQTT blocking during hardware handshake.
                    thread = threading.Thread(
                        target=self._connect_and_get_inst,
                        args=(resource,),
                        daemon=True,
                        name=f"VISA-Connect-{resource}"
                    )
                    thread.start()
                else:
                    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "No device selected to connect.", "DEBUG")
            else:
                matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "Ignoring GUI Connect Request, value is not 'true'.", "DEBUG")
        except (orjson.JSONDecodeError, AttributeError) as e:
            logger.error(f"Error in _on_gui_connect_request: {e}. Payload: {payload}")

    def _connect_and_get_inst(self, resource_name):
        """Internal helper to execute connection logic and store the session."""
        inst = self.connector.connect_instrument_logic(resource_name)
        with self._state_lock:
            self.inst = inst

    def _on_gui_disconnect_request(self, topic, payload):
        """Initiates a disconnection from the current instrument."""
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Trigger received for GUI Disconnect Request on topic: {topic}", "DEBUG")
        try:
            if not payload:
                matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Received empty payload for GUI Disconnect Request on topic: {topic}. Ignoring.", "DEBUG")
                return

            payload_data = orjson.loads(payload)
            if payload_data.get("value") is True:
                matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "Processing GUI Disconnect Request, value is 'true'.", "DEBUG")
                
                with self._state_lock:
                    inst_to_close = self.inst
                    self.inst = None
                
                if inst_to_close:
                    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "Initiating disconnection...", "DEBUG")
                    thread = threading.Thread(
                        target=self.disconnector.disconnect_instrument_logic,
                        args=(inst_to_close,),
                        daemon=True,
                        name="VISA-Disconnect"
                    )
                    thread.start()
                else:
                    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "No device is currently connected.", "DEBUG")
            else:
                matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "Ignoring GUI Disconnect Request, value is not 'true'.", "DEBUG")
        except Exception:
            logger.exception("Error in _on_gui_disconnect_request")

    def _on_connect_request(self, topic, payload):
        """Processes a direct command to connect to a specific VISA resource."""
        matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Trigger received for Direct Connect Request on topic: {topic}", "DEBUG")
        try:
            if not payload:
                matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Received empty payload for Direct Connect Request on topic: {topic}. Ignoring.", "DEBUG")
                return

            payload_data = orjson.loads(payload)
            resource_name = payload_data.get("resource")
            if resource_name:
                matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Processing Direct Connect Request for resource: {resource_name}", "DEBUG")
                thread = threading.Thread(
                    target=self._connect_and_get_inst,
                    args=(resource_name,),
                    daemon=True,
                    name=f"VISA-DirectConnect-{resource_name}"
                )
                thread.start()
            else:
                matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "Ignoring Direct Connect Request, no resource_name in payload.", "DEBUG")
        except orjson.JSONDecodeError:
            logger.error(f"Failed to decode JSON payload for connect request: {payload}")
        except Exception:
            logger.exception("Error in _on_connect_request")
