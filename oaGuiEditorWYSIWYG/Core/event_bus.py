import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# Core/event_bus.py
# Author: Gemini CLI
# Version: 1.1.0
#
# Description: A simple Publisher/Subscriber (Pub/Sub) event bus to decouple modular editor components.

from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

LOCAL_DEBUG = True


class EventBus:
    """A lightweight event bus for component communication."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance._subscribers = {}
            cls._instance.raise_exceptions = False
        return cls._instance

    def reset(self):
        """Clears all subscribers."""
        self._subscribers = {}
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🧹 EventBus: Reset complete. All subscribers cleared.", "DEBUG")

    def subscribe(self, event_type, callback):
        """Subscribes a callback to an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)
            cb_name = callback.__name__ if hasattr(callback, '__name__') else str(callback)
            matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🔔 EventBus: Subscribed '{cb_name}' to '{event_type}'.", "DEBUG")

    def unsubscribe(self, event_type, callback):
        """Unsubscribes a callback from an event type."""
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
                cb_name = callback.__name__ if hasattr(callback, '__name__') else str(callback)
                matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🔕 EventBus: Unsubscribed '{cb_name}' from '{event_type}'.", "DEBUG")

    def publish(self, event_type, **kwargs):
        """Publishes an event to all subscribers."""
        source = kwargs.get('source', 'Unknown')
        source_name = source.__class__.__name__ if not isinstance(source, str) else source
        
        subscriber_count = len(self._subscribers.get(event_type, []))
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"📢 EventBus: Publishing '{event_type}' from {source_name} to {subscriber_count} subscribers.", "DEBUG")
        
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(**kwargs)
                except Exception as e:
                    logger.exception(f"❌ EventBus Error: Callback failed for '{event_type}'")
                    if self.raise_exceptions:
                        raise e

# Global instance
event_bus = EventBus()
