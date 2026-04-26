# oaComProtocols.oaComNmos/Core/event_bus.py
# Author: Gemini (Collaborator)
# Version: 20260414.1130.1
#
# Description: Local Event Bus for NMOS standalone operation.
# ⚡ DECOUPLED: Does not depend on oaComBroker.

import threading
from collections.abc import Callable


class NmosEventBus:
    """
    A simple, thread-safe local event bus for the NMOS module.
    """
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribes a callback to an event type."""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribes a callback from an event type."""
        with self._lock:
            if event_type in self._subscribers:
                if callback in self._subscribers[event_type]:
                    self._subscribers[event_type].remove(callback)

    def publish(self, event_type: str, *args, **kwargs):
        """Publishes an event to all subscribers of that type."""
        with self._lock:
            callbacks = self._subscribers.get(event_type, []).copy()

        for callback in callbacks:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"[NmosEventBus] Error in callback for {event_type}: {e}")

# Global instance for the module
nmos_event_bus = NmosEventBus()
