# Core/registry_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import logging
import threading

from loguru import logger

try:
    from oaRustCore.oa_translator_core_rs import WidgetRegistry as RustWidgetRegistry
    HAS_RUST = True
except Exception as e:
    logging.warning(f"oaTranslator: Failed to load Rust WidgetRegistry: {e}")
    HAS_RUST = False

# Specialized logger bound to the state engine subsystem.
state_logger = logger.bind(subsystem="STATE_ENGINE")

class ThreadSafeRegistry:
    """Encapsulates thread-safe storage for widget registrations."""
    def __init__(self):
        if HAS_RUST:
            self._registry = RustWidgetRegistry()
        else:
            self._lock = threading.RLock()
            self.widgets = {}
            self.topic_map = {}

    def register(self, widget_id, info):
        if HAS_RUST:
            self._registry.register(widget_id, info)
        else:
            with self._lock:
                self.widgets[widget_id] = info
                self.topic_map[info["topic"]] = widget_id

    def is_registered(self, widget_id):
        if HAS_RUST:
            return self._registry.is_registered(widget_id)
        with self._lock:
            return widget_id in self.widgets

    def get_topic(self, widget_id):
        if HAS_RUST:
            return self._registry.get_topic(widget_id)
        with self._lock:
            return self.widgets.get(widget_id, {}).get("topic")

    def get_info(self, widget_id):
        if HAS_RUST:
            return self._registry.get_info(widget_id)
        with self._lock:
            return self.widgets.get(widget_id)

    @property
    def all_widgets(self):
        if HAS_RUST:
            return self._registry.all_widgets()
        return self.widgets

    @property
    def topic_to_widget_id(self):
        if HAS_RUST:
            return self._registry.all_topics()
        return self.topic_map

class RegistryMixin:
    """Manages the registration and lookup of GUI widgets and their mapped MQTT topics."""

    def _initialize_registry(self):
        self._registry = ThreadSafeRegistry()

    @property
    def registered_widgets(self):
        # Backward compatibility
        return self._registry.all_widgets

    @property
    def topic_to_widget_id(self):
        return self._registry.topic_to_widget_id

    def is_widget_registered(self, widget_id: str) -> bool:
        return self._registry.is_registered(widget_id)

    def get_widget_topic(self, widget_id):
        return self._registry.get_topic(widget_id)

    def _get_widget_info(self, widget_id):
        return self._registry.get_info(widget_id)

    def _register_to_internal_dicts(self, widget_id, info):
        self._registry.register(widget_id, info)
