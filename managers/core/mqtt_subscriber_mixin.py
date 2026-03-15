# managers/core/mqtt_subscriber_mixin.py
from loguru import logger

class MqttSubscriberMixin:
    """Provides centralized MQTT subscription management for backend modules."""

    def register_mqtt_topics(self, topic_map, subscriber_router=None):
        """
        Subscribes to multiple MQTT topics based on a mapping.
        
        Args:
            topic_map (dict): Mapping of {topic_filter: callback_func}.
            subscriber_router: Optional router instance. If None, uses self.subscriber_router.
        """
        router = subscriber_router or getattr(self, "subscriber_router", None)
        if not router:
            logger.error(f"{self.__class__.__name__}: No subscriber_router available for MQTT registration.")
            return

        for topic, callback in topic_map.items():
            try:
                router.subscribe_to_topic(topic_filter=topic, callback_func=callback)
                logger.trace(f"✅ {self.__class__.__name__}: Subscribed to '{topic}'")
            except Exception as e:
                logger.error(f"❌ {self.__class__.__name__}: Failed to subscribe to '{topic}': {e}")
