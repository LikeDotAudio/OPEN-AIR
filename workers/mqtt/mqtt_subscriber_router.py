# mqtt/mqtt_subscriber_router.py
#
# Manages MQTT subscriptions and dispatches incoming messages to registered callbacks.
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
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args


class MqttSubscriberRouter:
    # Initializes the MqttSubscriberRouter.
    # This sets up an internal dictionary to store topic filters and their
    # corresponding callback functions.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def __init__(self):
        self._subscribers = {}

    # Stores a callback function to be invoked when a message matching the topic filter is received.
    # This method registers a topic filter and its associated callback, but does not
    # immediately subscribe to the MQTT broker. Actual subscription occurs via `resubscribe_all_topics`.
    # Inputs:
    #     topic_filter (str): The MQTT topic filter to subscribe to.
    #     callback_func (function): The function to call when a message matching the filter is received.
    # Outputs:
    #     None.
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

    # Callback function for incoming MQTT messages.
    # This method is designed to be passed to the MQTT client. It decodes the payload
    # and dispatches the message to all registered callback functions whose topic filters match
    # the incoming message's topic.
    # Inputs:
    #     client: The Paho MQTT client instance.
    #     userdata: User-defined data passed to the callback.
    #     msg: The Paho MQTT message object.
    # Outputs:
    #     None.
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

    # Returns the internal `_on_message` method for use by the MQTT connection manager.
    # This provides the necessary callback for the Paho MQTT client to handle incoming messages.
    # Inputs:
    #     None.
    # Outputs:
    #     function: The `_on_message` method of this router instance.
    def get_on_message_callback(self):
        """
        Returns the _on_message method to be used by the MqttConnectionManager.
        """
        return self._on_message

    # Instructs the MQTT client to subscribe to all currently registered topic filters.
    # This method is typically called after the MQTT client has successfully connected
    # or reconnected to the broker to ensure all subscriptions are active.
    # Inputs:
    #     client: The Paho MQTT client instance.
    # Outputs:
    #     None.
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