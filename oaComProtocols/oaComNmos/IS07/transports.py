# FolderName/FileName.py
# Author: Gemini (Collaborator)
# Version: 20260405.1315.15 (updated)

import socket
import struct
import time
import uuid
import json
import hashlib
import requests
import ssl # For potential TLS in MQTT
# Removed: import websocket # For WebSocket client
# Removed: import threading # Only used by WebSocketEventTransport
import paho.mqtt.client as mqtt # For MQTT client

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Callable

# Import EventTransport from the new centralized location
from oaComProtocols.oaComWebsocket.Core.abc import EventTransport
# Import the WebSocketEventTransport from its new centralized location
from oaComProtocols.oaComWebsocket.Core.websocket_transport import WebSocketEventTransport

from oaComProtocols.oaComNmos.Core.utils import gen_id, get_ip, hash_sdp, now_ts
from oaComProtocols.oaComNmos.Core.sdp_parser import parse_sdp
from oaComProtocols.oaComNmos.Core.nmos_builder import build_source, build_flow, build_sender
from oaComProtocols.oaComNmos.Managers.sender_cache_manager import find_existing_sender
from oaComProtocols.oaComNmos.IS07.core_models import Message, EventCore, Identity, Timing, BooleanPayload, StringPayload, NumberPayload, ObjectPayload, GenericTypeDefinition
from oaComProtocols.oaComNmos.Constants import settings
from oaComProtocols.oaComNmos.Managers import registration_manager
from oaComProtocols.oaComNmos.Interface.connection_api import STREAMS # Access shared state dict from connection_api

# --- Abstract Base Classes for Transports ---

# EventTransport class is now imported from oaComProtocols.oaComWebsocket.Core.abc

# --- MQTT Transport Implementation ---

class MqttEventTransport(EventTransport):
    """
    Implements IS-07 event transport over MQTT.
    Requires 'paho-mqtt' library.
    """
    def __init__(self):
        super().__init__()
        self.client: Optional[mqtt.Client] = None
        self._on_connect_callback = self._on_connect
        self._on_message_callback = self._on_message
        self._on_disconnect_callback = self._on_disconnect
        print("[MQTTTransport] Initialized.")

    def publish(self, topic: str, payload: Dict[str, Any], retain: bool = False, qos: int = 0) -> bool:
        """Publishes a message to an MQTT topic."""
        if not self.is_connected() or not self.client:
            print("[MQTTTransport] Not connected. Cannot publish.")
            return False
        try:
            payload_str = json.dumps(payload)
            print(f"[MQTTTransport] Publishing to '{topic}' (retain={retain}, qos={qos}): {payload_str}")
            info = self.client.publish(topic, payload_str, qos=qos, retain=retain)
            return info.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            print(f"[MQTTTransport] Error publishing message: {e}")
            return False

    def subscribe(self, topic: str, qos: int = 0) -> bool:
        """Subscribes to an MQTT topic."""
        if not self.is_connected() or not self.client:
            print("[MQTTTransport] Not connected. Cannot subscribe.")
            return False
        try:
            print(f"[MQTTTransport] Subscribing to '{topic}' with QoS {qos}.")
            result, mid = self.client.subscribe(topic, qos=qos)
            return result == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            print(f"[MQTTTransport] Error subscribing to topic '{topic}': {e}")
            return False

    def unsubscribe(self, topic: str) -> bool:
        """Unsubscribes from an MQTT topic."""
        if not self.is_connected() or not self.client:
            print("[MQTTTransport] Not connected. Cannot unsubscribe.")
            return False
        try:
            print(f"[MQTTTransport] Unsubscribing from '{topic}'.")
            result, mid = self.client.unsubscribe(topic)
            return result == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            print(f"[MQTTTransport] Error unsubscribing from topic '{topic}': {e}")
            return False

    def connect(self, connection_params: Dict[str, Any]) -> bool:
        """Connects to the MQTT broker."""
        host = connection_params.get("destination_host", "localhost")
        port = connection_params.get("destination_port", 1883)
        protocol = connection_params.get("broker_protocol", "mqtt")
        auth = connection_params.get("broker_authorization", False)
        username = connection_params.get("username")
        password = connection_params.get("password")
        client_id = connection_params.get("client_id", gen_id()) # Allow specifying client_id

        print(f"[MQTTTransport] Attempting to connect to broker at {host}:{port} (protocol: {protocol}, auth: {auth}, client_id: {client_id}).")

        self.client = mqtt.Client(client_id=client_id)
        self.client.on_connect = self._on_connect_callback
        self.client.on_message = self._on_message_callback
        self.client.on_disconnect = self._on_disconnect_callback

        if protocol == "secure-mqtt":
            # Configure TLS - this is a basic example, real usage might need certs
            self.client.tls_set(tls_version=ssl.PROTOCOL_TLS)
        if auth and username and password:
            self.client.username_pw_set(username, password)
        
        try:
            self.client.connect(host, port, 60)
            self.client.loop_start() # Start network loop in a background thread
            # Give it a moment to connect
            time.sleep(1) 
            return self._is_connected # Return status after connection attempt
        except Exception as e:
            print(f"[MQTTTransport] Connection failed: {e}")
            self.client = None
            self._is_connected = False
            return False

    def disconnect(self):
        """Disconnects from the MQTT broker."""
        if self.client:
            print("[MQTTTransport] Disconnecting from broker.")
            self.client.loop_stop()
            self.client.disconnect()
            self.client = None
            self._is_connected = False
        else:
            print("[MQTTTransport] Not connected.")

    def set_message_handler(self, handler: Callable[[str, Dict[str, Any]], None]):
        """Sets the callback for handling incoming messages."""
        self._message_handler = handler
        print("[MQTTTransport] Message handler set.")

    def _on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection."""
        if rc == 0:
            print("[MQTTTransport] Connected successfully to MQTT Broker.")
            self._is_connected = True
            # This is where subscriptions should ideally happen after successful connection
            # For now, subscriptions are initiated by the caller.
        else:
            print(f"[MQTTTransport] Connection failed with result code {rc}.")
            self._is_connected = False

    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection."""
        print(f"[MQTTTransport] Disconnected from MQTT Broker with result code {rc}.")
        self._is_connected = False

    def _on_message(self, client, userdata, message):
        """Callback for received MQTT messages."""
        print(f"[MQTTTransport] Received message on topic {message.topic}: {message.payload.decode()}")
        if self._message_handler:
            try:
                payload_data = json.loads(message.payload.decode())
                self._message_handler(message.topic, payload_data)
            except json.JSONDecodeError:
                print(f"[MQTTTransport] Failed to decode JSON payload from topic {message.topic}.")
            except Exception as e:
                print(f"[MQTTTransport] Error processing received message: {e}")


# --- WebSocket Transport Implementation ---
# The WebSocketEventTransport class has been moved to oaComProtocols.oaComWebsocket.Core.websocket_transport

# --- IS-07 Core Logic ---

class Is07Bridge:
    """
    A bridge to handle IS-07 event and message publishing/subscribing.
    This class would integrate with the transports and the NMOS resource management.
    """
    def __init__(self, registrar_url: str):
        self.registrar_url = registrar_url
        self.mqtt_transport = MqttEventTransport()
        # Instantiate WebSocketEventTransport from the new shared module
        self.websocket_transport = WebSocketEventTransport() 
        self._message_handler: Optional[Callable[[str, Dict[str, Any]], None]] = None
        print("[IS07Bridge] Initialized.")

    def initialize_transports(self, connection_params_mqtt: Dict[str, Any], connection_params_ws: Dict[str, Any]):
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

    def shutdown(self):
        """Shuts down transport connections."""
        print("[IS07Bridge] Shutting down transports.")
        self.mqtt_transport.disconnect()
        self.websocket_transport.disconnect()

    def set_message_handler(self, handler: Callable[[str, Dict[str, Any]], None]):
        """Sets a global handler for all incoming IS-07 messages."""
        self._message_handler = handler
        print("[IS07Bridge] Global message handler set.")

    def _handle_incoming_message(self, transport_type: str, payload: Dict[str, Any]):
        """
        Handles incoming IS-07 messages from any transport.
        Parses the payload and dispatches it to the user-defined handler.
        """
        print(f"[IS07Bridge] Received message via {transport_type}: {payload}")
        if self._message_handler:
            try:
                # Attempt to parse the payload into known IS-07 structures.
                # This part requires more sophisticated parsing based on message_type.
                # For now, passing the raw payload.
                self._message_handler(transport_type, payload)
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


# --- IS-07 Core Logic ---

class Is07Bridge:
    """
    A bridge to handle IS-07 event and message publishing/subscribing.
    This class would integrate with the transports and the NMOS resource management.
    """
    def __init__(self, registrar_url: str):
        self.registrar_url = registrar_url
        self.mqtt_transport = MqttEventTransport()
        self.websocket_transport = WebSocketEventTransport()
        self._message_handler: Optional[Callable[[str, Dict[str, Any]], None]] = None
        print("[IS07Bridge] Initialized.")

    def initialize_transports(self, connection_params_mqtt: Dict[str, Any], connection_params_ws: Dict[str, Any]):
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

    def shutdown(self):
        """Shuts down transport connections."""
        print("[IS07Bridge] Shutting down transports.")
        self.mqtt_transport.disconnect()
        self.websocket_transport.disconnect()

    def set_message_handler(self, handler: Callable[[str, Dict[str, Any]], None]):
        """Sets a global handler for all incoming IS-07 messages."""
        self._message_handler = handler
        print("[IS07Bridge] Global message handler set.")

    def _handle_incoming_message(self, transport_type: str, payload: Dict[str, Any]):
        """
        Handles incoming IS-07 messages from any transport.
        Parses the payload and dispatches it to the user-defined handler.
        """
        print(f"[IS07Bridge] Received message via {transport_type}: {payload}")
        if self._message_handler:
            try:
                # Attempt to parse the payload into known IS-07 structures.
                # This part requires more sophisticated parsing based on message_type.
                # For now, passing the raw payload.
                self._message_handler(transport_type, payload)
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
