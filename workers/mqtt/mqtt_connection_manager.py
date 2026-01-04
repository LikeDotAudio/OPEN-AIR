# workers/mqtt/mqtt_connection_manager.py
#
# Purpose: Singleton. Maintains the socket connection to the broker. Handles the heartbeat.
# Key Function: get_client_instance() -> Returns the connected client.
# Key Function: connect_to_broker(address, port) -> Initiates the handshake.
# Logic: If the connection drops, IT handles the retry logic, not the GUI.

import paho.mqtt.client as mqtt
import threading
from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config                                                                          

app_constants = Config.get_instance() # Get the singleton instance      

class MqttConnectionManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, 'initialized'):
            return
        self.client = None
        self.initialized = True
        self.broker_address = None
        self.broker_port = None
        self.on_message_callback = None

    def get_client_instance(self):
        """Returns the connected client instance."""
        return self.client

    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the MQTT client connects to the broker."""
        if rc == 0:
            debug_logger(message="✅ Successfully connected to MQTT Broker.", **_get_log_args())
            if self.subscriber_router:
                # Tell the router to re-subscribe to all known topics
                self.subscriber_router.resubscribe_all_topics(client)
        else:
            debug_logger(message=f"❌ Failed to connect to MQTT Broker with result code {rc}", **_get_log_args())

    def connect_to_broker(self, address=None, port=None, on_message_callback=None, subscriber_router=None):
        """Connects the MQTT client to the broker."""
        if self.client and self.client.is_connected():
            debug_logger(message="🟡 MQTT client is already connected.", **_get_log_args())
            return

        self.broker_address = address if address is not None else app_constants.MQTT_BROKER_ADDRESS
        self.broker_port = port if port is not None else app_constants.MQTT_BROKER_PORT
        self.on_message_callback = on_message_callback
        self.subscriber_router = subscriber_router # Store subscriber_router

        try:
            self.client = mqtt.Client()
            self.client.on_connect = self.on_connect
            if self.on_message_callback:
                self.client.on_message = self.on_message_callback
            
            # Set Last Will and Testament
            self.client.will_set("OPEN-AIR/status", payload="OFFLINE", qos=1, retain=True)

            if app_constants.MQTT_USERNAME and app_constants.MQTT_PASSWORD:
                self.client.username_pw_set(app_constants.MQTT_USERNAME, app_constants.MQTT_PASSWORD)

            # Enable auto-reconnect
            self.client.reconnect_delay_set(min_delay=1, max_delay=15)

            self.client.connect(host=self.broker_address, port=self.broker_port, keepalive=60)
            self.client.loop_start()
            debug_logger(message="⚙️ MQTT client connection initiated in a background thread.", **_get_log_args())
        except Exception as e:
            debug_logger(message=f"❌ Error connecting to MQTT broker: {e}", **_get_log_args())

    def disconnect(self):
        """Disconnects the MQTT client from the broker."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            debug_logger(message="🔌 MQTT client disconnected.", **_get_log_args())