# workers/wysiwyg_editor/core/event_bus.py
#
# A simple Publisher/Subscriber (Pub/Sub) event bus to decouple modular editor components.
#
# Author: Gemini CLI

from oaLogging.logger import initialize_logging, set_log_directory
from loguru import logger

LOCAL_DEBUG = True    # Set to False in production, True for dev on this file


class EventBus:
    """A lightweight event bus for component communication."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance._subscribers = {}
        return cls._instance

    def subscribe(self, event_type, callback):
        """Subscribes a callback to an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)
            if LOCAL_DEBUG: logger.debug(f"🔔 EventBus: Subscribed '{callback.__name__ if hasattr(callback, '__name__') else 'lambda'}' to '{event_type}'.")

    def unsubscribe(self, event_type, callback):
        """Unsubscribes a callback from an event type."""
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
                if LOCAL_DEBUG: logger.debug(f"🔕 EventBus: Unsubscribed '{callback.__name__ if hasattr(callback, '__name__') else 'lambda'}' from '{event_type}'.")

    def publish(self, event_type, **kwargs):
        """Publishes an event to all subscribers."""
        source = kwargs.get('source', 'Unknown')
        source_name = source.__class__.__name__ if not isinstance(source, str) else source
        
        subscriber_count = len(self._subscribers.get(event_type, []))
        if LOCAL_DEBUG: logger.debug(f"📢 EventBus: Publishing '{event_type}' from {source_name} to {subscriber_count} subscribers.")
        
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(**kwargs)
                except Exception as e:
                    logger.exception("❌ EventBus Error: Callback failed for '{event_type}'")

# Global instance
event_bus = EventBus()
