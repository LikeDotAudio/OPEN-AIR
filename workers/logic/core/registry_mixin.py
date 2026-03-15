import threading
from loguru import logger

# Specialized logger bound to the state engine subsystem.
state_logger = logger.bind(subsystem="STATE_ENGINE")

class RegistryMixin:
    """Manages the registration and lookup of GUI widgets and their mapped MQTT topics."""

    def _initialize_registry(self):
        self._registry_lock = threading.RLock()
        self.registered_widgets = {}
        self.topic_to_widget_id = {}

    def is_widget_registered(self, widget_id: str) -> bool:
        with self._registry_lock:
            return widget_id in self.registered_widgets
            
    def get_widget_topic(self, widget_id):
        with self._registry_lock:
            if widget_id in self.registered_widgets:
                return self.registered_widgets[widget_id]["topic"]
            return None

    def _get_widget_info(self, widget_id):
        with self._registry_lock:
            return self.registered_widgets.get(widget_id)

    def _register_to_internal_dicts(self, widget_id, info):
        with self._registry_lock:
            self.registered_widgets[widget_id] = info
            self.topic_to_widget_id[info["topic"]] = widget_id
