# builder_core/gui_mqtt_manager.py
#
# Handles MQTT Context and Command Transmission.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20250821.200641.1
import time
import orjson
from workers.mqtt.mqtt_topic_utils import get_topic, generate_topic_path_from_filepath
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.setup.path_initializer import GLOBAL_PROJECT_ROOT


class GuiMqttManagerMixin:
    """Handles MQTT Context and Command Transmission."""

    # Initializes the MQTT context for the GUI.
    # This method determines the base MQTT topic for the GUI components based on the
    # file path of the JSON configuration, ensuring a logical topic hierarchy.
    # Inputs:
    #     json_filepath (str): The file path of the JSON configuration.
    #     app_constants: The application's configuration instance.
    #     base_mqtt_topic_from_path (str, optional): An override for the base MQTT topic.
    # Outputs:
    #     None.
    def _initialize_mqtt_context(
        self, json_filepath, app_constants, base_mqtt_topic_from_path=None
    ):
        if base_mqtt_topic_from_path:
            self.base_mqtt_topic_from_path = base_mqtt_topic_from_path
        elif json_filepath is None:
            self.base_mqtt_topic_from_path = "GENERIC_GUI_TOPIC"
        elif GLOBAL_PROJECT_ROOT is None:
            self.base_mqtt_topic_from_path = "FALLBACK_TOPIC"
        else:
            self.base_mqtt_topic_from_path = generate_topic_path_from_filepath(
                json_filepath, GLOBAL_PROJECT_ROOT
            )

        if self.state_mirror_engine and not hasattr(
            self.state_mirror_engine, "base_topic"
        ):
            self.state_mirror_engine.base_topic = app_constants.get_mqtt_base_topic()

    # Publishes the entire JSON configuration data to the base MQTT topic.
    # This allows other parts of the system to be aware of the GUI's structure and configuration.
    # Inputs:
    #     json_data (dict): The JSON data to be published.
    # Outputs:
    #     None.
    def _publish_json_to_topic(self, json_data):
        """Publishes the entire JSON data to the base topic."""
        if self.state_mirror_engine and self.base_mqtt_topic_from_path:
            payload = {
                "val": json_data,
                "src": "gui-init",
                "ts": time.time(),
                "GUID": self.state_mirror_engine.GUID,
            }
            self.state_mirror_engine.publish_command(
                get_topic(self.state_mirror_engine.base_topic, self.base_mqtt_topic_from_path), orjson.dumps(payload)
            )

    # Transmits a command or state change from a widget to the MQTT broker.
    # This centralized method handles the sending of GUI updates, either by broadcasting
    # a registered widget's state change or by publishing a command to a specific topic.
    # Inputs:
    #     widget_name (str): The name or ID of the widget sending the command.
    #     value: The value or state to be transmitted.
    # Outputs:
    #     None.
    def _transmit_command(self, widget_name: str, value):
        """Centralized method for sending GUI updates to MQTT."""
        if self.state_mirror_engine:
            if self.state_mirror_engine.is_widget_registered(widget_name):
                self.state_mirror_engine.broadcast_gui_change_to_mqtt(widget_name)
            else:
                topic = get_topic(
                    self.state_mirror_engine.base_topic,
                    self.base_mqtt_topic_from_path,
                    widget_name,
                )
                payload = {
                    "val": value,
                    "src": "gui",
                    "ts": time.time(),
                    "GUID": self.state_mirror_engine.GUID,
                }
                self.state_mirror_engine.publish_command(topic, orjson.dumps(payload))