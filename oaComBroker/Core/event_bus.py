# oaComBroker/Core/event_bus.py
# Author: Gemini CLI (Refactored)
# Version: 20260412.1130.1
#
# Description: Centralized Event Bus for cross-module communication.
#              Provides a lightweight Pub/Sub mechanism to decouple partitions.

import inspect
import threading
from collections.abc import Callable

from oaLogging.Methods.matrix_gate import matrix_log


class EventBus:
    """A singleton event bus for decoupled system-wide communication."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._subscribers = {}
                    cls._instance.raise_exceptions = False
        return cls._instance

    def reset(self):
        """Clears all subscribers."""
        self._subscribers = {}
        matrix_log(
            system="BROKER",
            element="EVENT_BUS",
            func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown",
            message="🔔🗃️💬 [EVENT_BUS] Reset complete. All subscribers cleared.",
            level="DEBUG",
        )

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribes a callback to an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)
            cb_name = callback.__name__ if hasattr(callback, '__name__') else str(callback)
            matrix_log(
                system="BROKER",
                element="EVENT_BUS",
                func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown",
                message=f"🔔🗃️💬 [EVENT_BUS] Subscribed '{cb_name}' to '{event_type}'.",
                level="DEBUG",
            )

    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribes a callback from an event type."""
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
                cb_name = callback.__name__ if hasattr(callback, '__name__') else str(callback)
                matrix_log(
                    system="BROKER",
                    element="EVENT_BUS",
                    func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown",
                    message=f"🔔🗃️💬 [EVENT_BUS] Unsubscribed '{cb_name}' from '{event_type}'.",
                    level="DEBUG",
                )

    def publish(self, event_type: str, **kwargs):
        """Publishes an event to all subscribers."""
        source = kwargs.get('source', 'Unknown')
        source_name = source.__class__.__name__ if not isinstance(source, str) else source

        subscriber_count = len(self._subscribers.get(event_type, []))
        matrix_log(
            system="BROKER",
            element="EVENT_BUS",
            func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown",
            message=f"🔔🗃️💬 [EVENT_BUS] Publishing '{event_type}' from {source_name} to {subscriber_count} subscribers.",
            level="DEBUG",
        )

        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(**kwargs)
                except Exception as e:
                    matrix_log(
                        system='BROKER',
                        element='EVENT_BUS',
                        func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown",
                        level='ERROR',
                        message=f"🔔🗃️💬 [EVENT_BUS] Callback failed for '{event_type}': {e}",
                    )
                    if self.raise_exceptions:
                        raise e

# Global instance for easy access
event_bus = EventBus()
