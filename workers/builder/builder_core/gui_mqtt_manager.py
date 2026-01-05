import time
import orjson
from workers.mqtt.mqtt_topic_utils import get_topic, generate_topic_path_from_filepath
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.setup.path_initializer import GLOBAL_PROJECT_ROOT

class GuiMqttManagerMixin:
    """Handles MQTT Context and Command Transmission."""

    def _initialize_mqtt_context(self, json_filepath, app_constants):
        if json_filepath is None:
            self.base_mqtt_topic_from_path = "GENERIC_GUI_TOPIC"
        elif GLOBAL_PROJECT_ROOT is None:
            self.base_mqtt_topic_from_path = "FALLBACK_TOPIC"
        else:
            self.base_mqtt_topic_from_path = generate_topic_path_from_filepath(json_filepath, GLOBAL_PROJECT_ROOT)

        if self.state_mirror_engine and not hasattr(self.state_mirror_engine, 'base_topic'):
            self.state_mirror_engine.base_topic = app_constants.get_mqtt_base_topic()

    def _transmit_command(self, widget_name: str, value):
        """Centralized method for sending GUI updates to MQTT."""
        if self.state_mirror_engine:
            if self.state_mirror_engine.is_widget_registered(widget_name):
                self.state_mirror_engine.broadcast_gui_change_to_mqtt(widget_name)
            else:
                topic = get_topic(self.state_mirror_engine.base_topic, self.base_mqtt_topic_from_path, widget_name)
                payload = {
                    "val": value,
                    "src": "gui",
                    "ts": time.time(),
                    "GUID": self.state_mirror_engine.GUID
                }
                self.state_mirror_engine.publish_command(topic, orjson.dumps(payload))
