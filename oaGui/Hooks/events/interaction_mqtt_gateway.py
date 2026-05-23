# oaGui/Hooks/interaction_interaction_interaction_mqtt_gateway.py
# Author: Anthony Peter Kuzub
# Version 20250821.200641.1
#
# Description: Gateway for incoming and outgoing MQTT broker traffic.

from oaComProtocols.oaComMQTT.Methods.mqtt_topic_utils import generate_topic_path_from_filepath
from oaGui.Hooks.events.interaction_dispatcher import InteractionDispatcher
from oaGui.Hooks.events.mqtt_rebuild_handler import MqttRebuildHandler
from oaOchestration.Constants.project_paths import GLOBAL_PROJECT_ROOT


class InteractionMqttGatewayMixin:
    """Gateway for incoming and outgoing MQTT broker traffic."""

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
        InteractionDispatcher.publish_init_state(self, json_data)

    def _publish_initial_widget_states(self, configuration):
        """Forces an initial MQTT announcement for all registered widgets."""
        if self.state_mirror_engine:
            self.state_mirror_engine.announce_all_widgets()

    def _transmit_command(self, widget_name: str, value):
        """Centralized method for sending GUI updates to MQTT."""
        InteractionDispatcher.transmit(self, widget_name, value)
