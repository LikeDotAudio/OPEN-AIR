# managers/VisaScipi/manager_visa_mqtt_listen.py
#
# This manager handles listening to MQTT topics for device connection and control.
# It acts as the bridge between external MQTT commands (GUI or automation)
# and the underlying VISA instrument management logic.
#
# Primary Responsibilities:
# - Monitor MQTT topics for device search, selection, and connection triggers.
# - Coordinate resource discovery and session management.
# - Offload blocking connection operations to background threads.
#
# Assumptions and Constraints:
# - Assumes a functional MQTT broker is reachable via the subscriber_router.
# - Payloads are expected to be JSON-encoded (orjson).
# - Threaded operations must not exceed system resource limits.
#
# Author: Anthony Peter Kuzub
#
import orjson
import threading

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

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
        """Initializes the VisaMqttListener with required services and state.

        Parameters:
        - subscriber_router: The service used to register for MQTT topic updates.
        - searcher: The component responsible for discovering VISA resources.
        - connector: The component that establishes instrument sessions.
        - disconnector: The component that terminates instrument sessions.
        - gui_publisher: The service used to broadcast state changes to the UI.

        Returns:
        - None.
        """
        self.subscriber_router = subscriber_router
        self.searcher = searcher
        self.connector = connector
        self.disconnector = disconnector
        self.gui_publisher = gui_publisher

        self.found_resources = []
        self.selected_device_resource = None
        self.inst = None

        self._setup_mqtt_subscriptions()

    def _setup_mqtt_subscriptions(self):
        """Registers callbacks for all relevant instrument control topics.

        Returns:
        - None.

        Side effects and thread-safety:
        - Modifies the subscriber_router state by adding multiple subscriptions.
        """
        try:
            self.subscriber_router.subscribe_to_topic(
                topic_filter=MQTT_TOPIC_SEARCH_TRIGGER,
                callback_func=self._on_search_request,
            )
            if LOCAL_DEBUG: logger.debug(f"💳 Subscribed to: {MQTT_TOPIC_SEARCH_TRIGGER}")
            self.subscriber_router.subscribe_to_topic(
                topic_filter=MQTT_TOPIC_DEVICE_SELECT,
                callback_func=self._on_device_select,
            )
            if LOCAL_DEBUG: logger.debug(f"💳 Subscribed to: {MQTT_TOPIC_DEVICE_SELECT}")
            self.subscriber_router.subscribe_to_topic(
                topic_filter=MQTT_TOPIC_CONNECT_TRIGGER,
                callback_func=self._on_gui_connect_request,
            )
            if LOCAL_DEBUG: logger.debug(f"💳 Subscribed to: {MQTT_TOPIC_CONNECT_TRIGGER}")
            self.subscriber_router.subscribe_to_topic(
                topic_filter=MQTT_TOPIC_DISCONNECT_TRIGGER,
                callback_func=self._on_gui_disconnect_request,
            )
            if LOCAL_DEBUG: logger.debug(f"💳 Subscribed to: {MQTT_TOPIC_DISCONNECT_TRIGGER}")
            self.subscriber_router.subscribe_to_topic(
                topic_filter=MQTT_TOPIC_CONNECT_RESOURCE_REQUEST,
                callback_func=self._on_connect_request,
            )
            if LOCAL_DEBUG: logger.debug(f"💳 Subscribed to: {MQTT_TOPIC_CONNECT_RESOURCE_REQUEST}")
            if LOCAL_DEBUG: logger.success("💳 ✅ VisaMqttListener subscribed to all necessary GUI and command topics.")
        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception("💳 ❌ Error in VisaMqttListener._setup_mqtt_subscriptions")

    def _on_search_request(self, topic, payload):
        """Processes a request to search for available VISA instruments.

        Parameters:
        - topic: The MQTT topic where the trigger was received.
        - payload: JSON bytes containing a "val" key (True to trigger search).

        Returns:
        - None.

        Side effects and thread-safety:
        - Updates self.found_resources with the search results.
        - Triggers a GUI update via gui_publisher.
        """
        if LOCAL_DEBUG: logger.debug(f"💳 Trigger received for Search Request on topic: {topic}. Payload: {payload}")
        try:
            if not payload:
                # Handle potential retained message cleanup by ignoring empty
                # payloads.
                if LOCAL_DEBUG: logger.debug(f"💳 🟡 Received empty payload for Search Request on topic: {topic}. Ignoring (likely retained message deletion).")
                return

            payload_data = orjson.loads(payload)
            if payload_data.get("val") is True:
                if LOCAL_DEBUG: logger.debug(f"💳 Processing Search for devices initiated from GUI. Payload Data: {orjson.dumps(payload_data).decode()}")
                self.found_resources = self.searcher.search_resources()
                self.gui_publisher._update_found_devices_gui(self.found_resources)
            else:
                if LOCAL_DEBUG: logger.debug(f"💳 Ignoring Search Request, value is not 'true'. Payload Data: {orjson.dumps(payload_data).decode()}")
        except (orjson.JSONDecodeError, AttributeError) as e:
            logger.error(f"💳 ❌ Error in _on_search_request: {e}. Payload: {payload}")

    def _on_device_select(self, topic, payload):
        """Updates the selected instrument resource based on GUI selection.

        Parameters:
        - topic: The MQTT topic containing the option index.
        - payload: JSON bytes containing a "value" key (True if selected).

        Returns:
        - None.

        Side effects and thread-safety:
        - Updates self.selected_device_resource.
        """
        if LOCAL_DEBUG: logger.debug(f"💳 Trigger received for Device Select on topic: {topic}. Payload: {payload}")
        try:
            if not payload:
                if LOCAL_DEBUG: logger.debug(f"💳 🟡 Received empty payload for Device Select on topic: {topic}. Ignoring (likely retained message deletion).")
                return

            payload_data = orjson.loads(payload)
            if payload_data.get("value") is True:
                if LOCAL_DEBUG: logger.debug(f"💳 Processing Device Select, value is 'true'. Payload Data: {orjson.dumps(payload_data).decode()}")
                # Extract the index from the topic structure: .../options/<index>/selected
                parts = topic.split("/")
                option_index = int(parts[-2]) - 1
                if 0 <= option_index < len(self.found_resources):
                    self.selected_device_resource = self.found_resources[option_index]
                    if LOCAL_DEBUG: logger.success(f"💳 ✅ Device selected: {self.selected_device_resource}")
                else:
                    self.selected_device_resource = None
            else:
                if LOCAL_DEBUG: logger.debug(f"💳 Ignoring Device Select, value is not 'true'. Payload Data: {orjson.dumps(payload_data).decode()}")
        except (orjson.JSONDecodeError, IndexError, ValueError, AttributeError) as e:
            logger.error(f"💳 ❌ Error in _on_device_select: {e}. Payload: {payload}")

    def _on_gui_connect_request(self, topic, payload):
        """Initiates a connection to the selected device from the GUI.

        Parameters:
        - topic: The MQTT topic.
        - payload: JSON bytes containing a "value" key.

        Returns:
        - None.

        Side effects and thread-safety:
        - Spawns a background thread to handle blocking I/O during connection.
        """
        if LOCAL_DEBUG: logger.debug(f"💳 Trigger received for GUI Connect Request on topic: {topic}. Payload: {payload}")
        try:
            if not payload:
                if LOCAL_DEBUG: logger.debug(f"💳 🟡 Received empty payload for GUI Connect Request on topic: {topic}. Ignoring (likely retained message deletion).")
                return

            payload_data = orjson.loads(payload)
            if payload_data.get("value") is True:
                if LOCAL_DEBUG: logger.debug(f"💳 Processing GUI Connect Request, value is 'true'. Payload Data: {orjson.dumps(payload_data).decode()}")
                if self.selected_device_resource:
                    if LOCAL_DEBUG: logger.debug(f"💳 🔵 Initiating connection to {self.selected_device_resource}...")
                    # Offload to thread to prevent MQTT blocking during hardware
                    # handshake.
                    thread = threading.Thread(
                        target=self._connect_and_get_inst,
                        args=(self.selected_device_resource,),
                        daemon=True,
                    )
                    thread.start()
                else:
                    if LOCAL_DEBUG: logger.debug("💳 🟡 No device selected to connect.")
            else:
                if LOCAL_DEBUG: logger.debug(f"💳 Ignoring GUI Connect Request, value is not 'true'. Payload Data: {orjson.dumps(payload_data).decode()}")
        except (orjson.JSONDecodeError, AttributeError) as e:
            logger.error(f"💳 ❌ Error in _on_gui_connect_request: {e}. Payload: {payload}")

    def _connect_and_get_inst(self, resource_name):
        """Internal helper to execute connection logic and store the session.

        Parameters:
        - resource_name: The VISA resource address.

        Returns:
        - None.

        Side effects and thread-safety:
        - Updates self.inst with the new resource session.
        """
        self.inst = self.connector.connect_instrument_logic(resource_name)

    def _on_gui_disconnect_request(self, topic, payload):
        """Initiates a disconnection from the current instrument.

        Parameters:
        - topic: The MQTT topic.
        - payload: JSON bytes.

        Returns:
        - None.

        Side effects and thread-safety:
        - Spawns a background thread to handle blocking disconnection I/O.
        """
        if LOCAL_DEBUG: logger.debug(f"💳 Trigger received for GUI Disconnect Request on topic: {topic}. Payload: {payload}")
        try:
            if not payload:
                if LOCAL_DEBUG: logger.debug(f"💳 🟡 Received empty payload for GUI Disconnect Request on topic: {topic}. Ignoring (likely retained message deletion).")
                return

            payload_data = orjson.loads(payload)
            if payload_data.get("value") is True:
                if LOCAL_DEBUG: logger.debug(f"💳 Processing GUI Disconnect Request, value is 'true'. Payload Data: {orjson.dumps(payload_data).decode()}")
                if self.inst:
                    if LOCAL_DEBUG: logger.debug("💳 🔵 Initiating disconnection...")
                    thread = threading.Thread(
                        target=self.disconnector.disconnect_instrument_logic,
                        args=(self.inst,),
                        daemon=True,
                    )
                    thread.start()
                    self.inst = None
                else:
                    if LOCAL_DEBUG: logger.debug("💳 🟡 No device is currently connected.")
            else:
                if LOCAL_DEBUG: logger.debug(f"💳 Ignoring GUI Disconnect Request, value is not 'true'. Payload Data: {orjson.dumps(payload_data).decode()}")
        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception("💳 ❌ Error in _on_gui_disconnect_request: . Payload: {payload}")

    def _on_connect_request(self, topic, payload):
        """Processes a direct command to connect to a specific VISA resource.

        Parameters:
        - topic: The MQTT topic.
        - payload: JSON bytes containing a "resource" key.

        Returns:
        - None.

        Side effects and thread-safety:
        - Spawns a background thread for connection.
        """
        if LOCAL_DEBUG: logger.debug(f"💳 Trigger received for Direct Connect Request on topic: {topic}. Payload: {payload}")
        try:
            if not payload:
                if LOCAL_DEBUG: logger.debug(f"💳 🟡 Received empty payload for Direct Connect Request on topic: {topic}. Ignoring (likely retained message deletion).")
                return

            payload_data = orjson.loads(payload)
            resource_name = payload_data.get("resource")
            if resource_name:
                if LOCAL_DEBUG: logger.debug(f"💳 Processing Direct Connect Request for resource: {resource_name}. Payload Data: {orjson.dumps(payload_data).decode()}")
                thread = threading.Thread(
                    target=self._connect_and_get_inst,
                    args=(resource_name,),
                    daemon=True,
                )
                thread.start()
            else:
                if LOCAL_DEBUG: logger.debug(f"💳 Ignoring Direct Connect Request, no resource_name in payload. Payload Data: {orjson.dumps(payload_data).decode()}")
        except orjson.JSONDecodeError:
            logger.error(f"💳 ❌ Failed to decode JSON payload for connect request: {payload}")
        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception("💳 ❌ Error in _on_connect_request: . Payload: {payload}")
