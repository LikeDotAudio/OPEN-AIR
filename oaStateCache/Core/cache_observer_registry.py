# Core/cache_observer_registry.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

class CacheObserverRegistry:
    """Manages the registration and notification of state change observers."""

    def __init__(self):
        self._observers = []

    def register_observer(self, callback):
        if callback not in self._observers: self._observers.append(callback)

    def remove(self, callback):
        if callback in self._observers: self._observers.remove(callback)

    def notify(self, topic, payload):
        from oaLogging.Entry import vocal_capture
        for cb in self._observers:
            try: 
                cb(topic, payload)
            except Exception:
                vocal_capture("CACHE", f"Observer callback '{cb.__name__}' failed during notification on topic '{topic}'")
