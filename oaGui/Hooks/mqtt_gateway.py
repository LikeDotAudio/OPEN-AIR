# Hooks/gui_mqtt.py
# Author: Anthony Peter Kuzub
# Version 20250821.200641.1
#
# Description: Handles MQTT Context and Command Transmission.

from oaComProtocols.oaComMQTT.Methods.mqtt_topic_utils import generate_topic_path_from_filepath
from oaOchestration.Constants.project_paths import GLOBAL_PROJECT_ROOT
from oaGui.Hooks.mqtt_rebuild_handler import MqttRebuildHandler
from oaGui.Hooks.mqtt_command_transmitter import MqttCommandTransmitter

class GuiMqttManagerMixin:
    """Handles MQTT Context and Command Transmission."""

    def _initialize_mqtt_context(
        self, json_filepath, app_constants, base_mqtt_topic_from_path=None
    ):
        """Initializes the MQTT context for the GUI."""
        if json_filepath is None or GLOBAL_PROJECT_ROOT is None:
            self.base_mqtt_topic_from_path = "GUI"
        else:
            self.base_mqtt_topic_from_path = generate_topic_path_from_filepath(
                json_filepath, GLOBAL_PROJECT_ROOT
            )

        if self.state_mirror_engine and not hasattr(self.state_mirror_engine, "base_topic"):
            self.state_mirror_engine.base_topic = app_constants.get_mqtt_base_topic()

        self._subscribe_to_rebuild_requests()

    def _subscribe_to_rebuild_requests(self):
        """Subscribes to the UI Rebuild topic for live updates."""
        if not self.subscriber_router or not self.json_filepath:
            return

        rebuild_topic = "OPEN-AIR/System/Control/UI/Rebuild"
        self.subscriber_router.subscribe_to_topic(
            rebuild_topic, 
            lambda msg: MqttRebuildHandler.handle_request(self, msg)
        )

    def _publish_json_to_topic(self, json_data):
        """Publishes the entire JSON configuration data to the base MQTT topic."""
        MqttCommandTransmitter.publish_init_state(self, json_data)

    def _publish_initial_widget_states(self, config_data):
        """Forces an initial MQTT announcement for all registered widgets."""
        if self.state_mirror_engine:
            self.state_mirror_engine.announce_all_widgets()

    def _transmit_command(self, widget_name: str, value):
        """Centralized method for sending GUI updates to MQTT."""
        MqttCommandTransmitter.transmit(self, widget_name, value)
