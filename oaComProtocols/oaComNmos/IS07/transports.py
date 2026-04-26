# FolderName/FileName.py
# Author: Gemini (Collaborator)
# Version: 20260405.1315.15 (updated)

# Removed: import websocket # For WebSocket client
# Removed: import threading # Only used by WebSocketEventTransport

from collections.abc import Callable
from typing import Any

from oaComProtocols.oaComNmos.Constants import settings

# ⚡ NATIVE CORE TRANSPORTS
from oaComProtocols.oaComNmos.Core.is07_transport import Is07MqttTransport, Is07WebSocketTransport
from oaComProtocols.oaComNmos.IS07.core_models import EventCore, Identity, Timing

# --- Abstract Base Classes for Transports ---

# --- IS-07 Core Logic ---

class Is07Bridge:
    """
    A bridge to handle IS-07 event and message publishing/subscribing.
    This class would integrate with the transports and the NMOS resource management.
    """
    def __init__(self, registrar_url: str):
        self.registrar_url = registrar_url
        self.mqtt_transport = Is07MqttTransport()
        # Instantiate native NMOS Core WebSocket transport
        self.websocket_transport = Is07WebSocketTransport()
        self._message_handler: Callable[[str, dict[str, Any]], None] | None = None
        print("[IS07Bridge] Initialized (Core Transports).")

    def initialize_transports(self, connection_params_mqtt: dict[str, Any], connection_params_ws: dict[str, Any]):
        """Initializes and connects the transport clients."""
        # Connect MQTT
        mqtt_connected = self.mqtt_transport.connect(connection_params_mqtt)
        # Connect WebSocket
        ws_connected = self.websocket_transport.connect(connection_params_ws)

        # Set message handlers for each transport if connection was successful
        if mqtt_connected:
            self.mqtt_transport.set_message_handler(self._handle_incoming_message)
        if ws_connected:
            self.websocket_transport.set_message_handler(self._handle_incoming_message)

    def start(self):
        """Starts the bridge and its transports with default parameters."""
        # Use default connection parameters for standalone operation
        mqtt_params = {
            "destination_host": "localhost",
            "destination_port": 1883
        }
        ws_params = {
            "connection_uri": f"ws://localhost:{settings.PORT}/is07"
        }
        self.initialize_transports(mqtt_params, ws_params)

    def stop(self):
        """Stops the bridge and its transports."""
        self.shutdown()

    @property
    def is_running(self) -> bool:
        """Returns True if the bridge is currently running (any transport connected)."""
        return self.mqtt_transport.is_connected() or self.websocket_transport.is_connected()

    def shutdown(self):
        """Shuts down transport connections."""
        print("[IS07Bridge] Shutting down transports.")
        self.mqtt_transport.disconnect()
        self.websocket_transport.disconnect()

    def set_message_handler(self, handler: Callable[[str, Any, dict[str, Any]], None]):
        """
        Sets a global handler for all incoming IS-07 and monitoring messages.
        Expected signature: handler(transport_type, topic, payload)
        """
        self._message_handler = handler
        print("[IS07Bridge] Global message handler set.")

    def _handle_incoming_message(self, topic_or_transport: str, payload: Any):
        """
        Handles incoming messages from any transport.
        Dispatches to the user-defined handler with transport context.
        """
        if self._message_handler:
            try:
                # ⚡ DISPATCH LOGIC:
                # If topic_or_transport starts with OPEN-AIR, it's likely an MQTT topic
                # Otherwise, it's a transport type label (e.g., 'websocket')
                if topic_or_transport.startswith("OPEN-AIR/"):
                    self._message_handler("mqtt", topic_or_transport, payload)
                else:
                    self._message_handler(topic_or_transport, None, payload)
            except Exception as e:
                print(f"[IS07Bridge] Error processing incoming message: {e}")

    # --- Publishing Methods ---

    def publish_state_change(self, identity: Identity, timing: Timing, event_type: str, payload: Any, transport_topic: str, transport_type: str = "mqtt") -> bool:
        """Publishes a state change event. Returns True on success, False otherwise."""
        # Ensure payload is correctly structured before converting to dict
        if isinstance(payload, (bool, str, int, float)):
            payload_data = {"value": payload}
        elif isinstance(payload, dict):
            payload_data = payload
        else:
            print(f"[IS07Bridge] Unsupported payload type for state change: {type(payload)}")
            return False

        event_data = EventCore(identity=identity, timing=timing, event_type=event_type, payload=payload_data)
        message_dict = event_data.__dict__ # Convert dataclass to dict for JSON serialization

        if transport_type == "mqtt":
            return self.mqtt_transport.publish(transport_topic, message_dict, retain=True)
        elif transport_type == "websocket":
            # For WebSocket, 'topic' is conceptual, often sending to a connected client session.
            return self.websocket_transport.publish(transport_topic, message_dict)
        else:
            print(f"[IS07Bridge] Unsupported transport type for publishing: {transport_type}")
            return False

    def publish_reboot_shutdown(self, identity: Identity, timing: Timing, message_type: str, transport_topic: str, transport_type: str = "mqtt") -> bool:
        """Publishes a reboot or shutdown message. Returns True on success, False otherwise."""
        if message_type not in ["reboot", "shutdown"]:
            print(f"[IS07Bridge] Invalid message_type for reboot/shutdown: {message_type}")
            return False

        message_data = MessageShutdownReboot(identity=identity, timing=timing, message_type=message_type)
        message_dict = message_data.__dict__

        if transport_type == "mqtt":
            return self.mqtt_transport.publish(transport_topic, message_dict, retain=False) # Reboot/Shutdown typically not retained
        elif transport_type == "websocket":
            return self.websocket_transport.publish(transport_topic, message_dict)
        else:
            print(f"[IS07Bridge] Unsupported transport type for publishing: {transport_type}")
            return False

    # ... potentially other publish methods for connection_status, health, etc. ...

    # --- Subscribing Methods ---

    def subscribe_to_events(self, topic: str, transport_type: str = "mqtt") -> bool:
        """Subscribes to event messages. Returns True on success, False otherwise."""
        if transport_type == "mqtt":
            return self.mqtt_transport.subscribe(topic)
        elif transport_type == "websocket":
            # WebSocket subscription is typically handled differently, e.g., via messages after connection
            print("[IS07Bridge] WebSocket subscription is managed via connection and explicit subscription messages, not a separate call.")
            return True # Assume success for now, actual message sending is a publish action
        else:
            print(f"[IS07Bridge] Unsupported transport type for subscribing: {transport_type}")
            return False

    def unsubscribe_from_events(self, topic: str, transport_type: str = "mqtt") -> bool:
        """Unsubscribes from event messages. Returns True on success, False otherwise."""
        if transport_type == "mqtt":
            return self.mqtt_transport.unsubscribe(topic)
        elif transport_type == "websocket":
            return True
        else:
            print(f"[IS07Bridge] Unsupported transport type for unsubscribing: {transport_type}")
            return False

    # --- Integration Point ---
    # This is where the IS-07 logic would integrate with the existing NMOS resource management.
    # For example, when an IS-07 event indicates a change in an NMOS resource's state,
    # this bridge could update the corresponding NMOS resource or trigger actions.

    def integrate_with_nmos(self, nmos_resource_manager):
        """
        Sets up integration with the NMOS resource manager.
        This is a conceptual placeholder.
        """
        print("[IS07Bridge] Integrating with NMOS resource manager (conceptual).")
        # Example:
        # def on_is07_event(transport_type, payload):
        #     # Parse payload, find corresponding NMOS resource, update its state or trigger action.
        #     print(f"Received IS-07 event: {payload}")
        #     # Example: if payload.get("message_type") == "state": ...
        #     pass
        # self.set_message_handler(on_is07_event)
