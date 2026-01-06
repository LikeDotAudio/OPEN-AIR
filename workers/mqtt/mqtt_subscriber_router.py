# workers/mqtt/mqtt_subscriber_router.py
#
# Purpose: The ear. Listens to topics and routes them to a callback.
# Key Function: subscribe_to_topic(topic: str, callback_function)
# Key Function: _on_message(client, userdata, msg) -> Decodes the byte payload and fires the callback.

import paho.mqtt.client as mqtt
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args


class MqttSubscriberRouter:
    def __init__(self):
        self._subscribers = {}

    def subscribe_to_topic(self, topic_filter: str, callback_func):
        """
        Stores a callback function for a given topic filter for later subscription.
        Actual subscription happens when the client connects/reconnects.
        """
        self._subscribers[topic_filter] = callback_func
        debug_logger(
            message=f"📝 Topic '{topic_filter}' added to pending subscriptions.",
            **_get_log_args(),
        )

    def _on_message(self, client, userdata, msg):
        """
        Callback for when an MQTT message is received.
        It decodes the message and dispatches it to the appropriate subscriber.
        """
        # TEMP: Raw print to definitively check if messages reach here

        # Log that a message was received at the router level
        debug_logger(
            message=f"📨 MQTT Message Received: Topic='{msg.topic}', Payload='{msg.payload}'",
            **_get_log_args(),
        )

        topic = msg.topic
        try:
            payload = msg.payload.decode()
        except UnicodeDecodeError:
            debug_logger(
                message=f"❌ Could not decode payload for topic {topic}",
                **_get_log_args(),
            )
            return

        for topic_filter, callback_func in list(
            self._subscribers.items()
        ):  # Iterate over a copy
            if mqtt.topic_matches_sub(topic_filter, topic):
                try:
                    callback_func(topic, payload)
                except Exception as e:
                    debug_logger(
                        message=f"❌ Error in callback for topic {topic}: {e}",
                        **_get_log_args(),
                    )

    def get_on_message_callback(self):
        """
        Returns the _on_message method to be used by the MqttConnectionManager.
        """
        return self._on_message

    def resubscribe_all_topics(self, client):
        """
        Instructs the MQTT client to subscribe to all topics registered with this router.
        This is typically called after a successful connection/reconnection.
        """
        for topic_filter in list(self._subscribers.keys()):  # Iterate over a copy
            client.subscribe(topic_filter)
            debug_logger(
                message=f"🔄 Resubscribed to {topic_filter}", **_get_log_args()
            )
