# Core/registry_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import threading
from loguru import logger

# Specialized logger bound to the state engine subsystem.
state_logger = logger.bind(subsystem="STATE_ENGINE")

class ThreadSafeRegistry:
    """Encapsulates thread-safe storage for widget registrations."""
    def __init__(self):
        self._lock = threading.RLock()
        self.widgets = {}
        self.topic_map = {}

    def register(self, widget_id, info):
        with self._lock:
            self.widgets[widget_id] = info
            self.topic_map[info["topic"]] = widget_id

    def is_registered(self, widget_id):
        with self._lock:
            return widget_id in self.widgets

    def get_topic(self, widget_id):
        with self._lock:
            return self.widgets.get(widget_id, {}).get("topic")

    def get_info(self, widget_id):
        with self._lock:
            return self.widgets.get(widget_id)

class RegistryMixin:
    """Manages the registration and lookup of GUI widgets and their mapped MQTT topics."""

    def _initialize_registry(self):
        self._registry = ThreadSafeRegistry()

    @property
    def registered_widgets(self):
        # Backward compatibility if needed, though direct access should be discouraged
        return self._registry.widgets

    @property
    def topic_to_widget_id(self):
        return self._registry.topic_map

    def is_widget_registered(self, widget_id: str) -> bool:
        return self._registry.is_registered(widget_id)
            
    def get_widget_topic(self, widget_id):
        return self._registry.get_topic(widget_id)

    def _get_widget_info(self, widget_id):
        return self._registry.get_info(widget_id)

    def _register_to_internal_dicts(self, widget_id, info):
        self._registry.register(widget_id, info)
