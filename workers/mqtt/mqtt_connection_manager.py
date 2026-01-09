# mqtt/mqtt_connection_manager.py
#
# Manages the singleton MQTT client connection to the broker, handles connection lifecycle, and provides client instance access.
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
# Version 20250821.200641.1

import paho.mqtt.client as mqtt
import threading
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance


class MqttConnectionManager:
    _instance = None
    _lock = threading.Lock()

    # Implements the singleton pattern for MqttConnectionManager.
    # This ensures that only one instance of the connection manager exists throughout
    # the application, preventing multiple MQTT client connections.
    # Inputs:
    #     cls: The class itself.
    #     *args: Positional arguments for the constructor.
    #     **kwargs: Keyword arguments for the constructor.
    # Outputs:
    #     MqttConnectionManager: The singleton instance of the class.
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    # Initializes the MqttConnectionManager instance.
    # This constructor sets up the basic properties of the manager, but only
    # performs initialization once due to the singleton pattern.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def __init__(self):
        if hasattr(self, "initialized"):
            return
        self.client = None
        self.initialized = True
        self.broker_address = None
        self.broker_port = None
        self.on_message_callback = None

    # Returns the connected Paho MQTT client instance.
    # This method provides access to the underlying MQTT client object, allowing
    # other parts of the application to interact directly with the broker (e.g., publish messages).
    # Inputs:
    #     None.
    # Outputs:
    #     mqtt.Client: The connected MQTT client instance.
    def get_client_instance(self):
        """Returns the connected client instance."""
        return self.client

    # Callback function executed when the MQTT client successfully connects to the broker.
    # If the connection is successful, it logs a success message and triggers the
    # subscriber router to re-subscribe to all known topics.
    # Inputs:
    #     client: The Paho MQTT client instance.
    #     userdata: User-defined data passed to the callback.
    #     flags: Response flags sent by the broker.
    #     rc (int): The connection result code (0 for success).
    # Outputs:
    #     None.
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the MQTT client connects to the broker."""
        if rc == 0:
            debug_logger(
                message="✅ Successfully connected to MQTT Broker.", **_get_log_args()
            )
            if self.subscriber_router:
                # Tell the router to re-subscribe to all known topics
                self.subscriber_router.resubscribe_all_topics(client)
        else:
            debug_logger(
                message=f"❌ Failed to connect to MQTT Broker with result code {rc}",
                **_get_log_args(),
            )

    # Initiates a connection to the MQTT broker.
    # This method configures the MQTT client with broker details, sets up callbacks
    # for connection and message reception, and starts the network loop in a
    # background thread to maintain the connection.
    # Inputs:
    #     address (str, optional): The broker's IP address or hostname.
    #     port (int, optional): The broker's port number.
    #     on_message_callback (function, optional): A callback function for incoming messages.
    #     subscriber_router (object, optional): An instance of the subscriber router.
    # Outputs:
    #     None.
    def connect_to_broker(
        self, address=None, port=None, on_message_callback=None, subscriber_router=None
    ):
        """Connects the MQTT client to the broker."""
        if self.client and self.client.is_connected():
            debug_logger(
                message="🟡 MQTT client is already connected.", **_get_log_args()
            )
            return

        self.broker_address = (
            address if address is not None else app_constants.MQTT_BROKER_ADDRESS
        )
        self.broker_port = port if port is not None else app_constants.MQTT_BROKER_PORT
        self.on_message_callback = on_message_callback
        self.subscriber_router = subscriber_router  # Store subscriber_router

        try:
            self.client = mqtt.Client()
            self.client.on_connect = self.on_connect
            if self.on_message_callback:
                self.client.on_message = self.on_message_callback

            # Set Last Will and Testament
            self.client.will_set(
                "OPEN-AIR/status", payload="OFFLINE", qos=1, retain=True
            )

            if app_constants.MQTT_USERNAME and app_constants.MQTT_PASSWORD:
                self.client.username_pw_set(
                    app_constants.MQTT_USERNAME, app_constants.MQTT_PASSWORD
                )

            # Enable auto-reconnect
            self.client.reconnect_delay_set(min_delay=1, max_delay=15)

            self.client.connect(
                host=self.broker_address, port=self.broker_port, keepalive=60
            )
            self.client.loop_start()
            debug_logger(
                message="⚙️ MQTT client connection initiated in a background thread.",
                **_get_log_args(),
            )
        except Exception as e:
            debug_logger(
                message=f"❌ Error connecting to MQTT broker: {e}", **_get_log_args()
            )

    # Disconnects the MQTT client from the broker.
    # This method stops the network loop and gracefully disconnects the client,
    # terminating the MQTT session.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def disconnect(self):
        """Disconnects the MQTT client from the broker."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            debug_logger(message="🔌 MQTT client disconnected.", **_get_log_args())