# Managers/gui_mqtt.py
from oaGui.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: Handles MQTT Context and Command Transmission.

import time
import orjson
from pathlib import Path

from oaLogging.Methods.matrix_gate import is_debug_allowed, matrix_log

def _is_debug():
    return is_debug_allowed(system="UI", element="MQTT")

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants_config = Config.get_instance()

from oaComProtocols.oaComMQTT.Methods.mqtt_topic_utils import get_topic, generate_topic_path_from_filepath
from oaOchestration.Constants.project_paths import GLOBAL_PROJECT_ROOT


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
        if json_filepath is None:
            self.base_mqtt_topic_from_path = "GUI"
        elif GLOBAL_PROJECT_ROOT is None:
            self.base_mqtt_topic_from_path = "GUI"
        else:
            self.base_mqtt_topic_from_path = generate_topic_path_from_filepath(
                json_filepath, GLOBAL_PROJECT_ROOT
            )

        if self.state_mirror_engine and not hasattr(
            self.state_mirror_engine, "base_topic"
        ):
            self.state_mirror_engine.base_topic = app_constants.get_mqtt_base_topic()
        
        # ⚡ REMOTE REBUILD: Listen for test requests from external editors
        self._subscribe_to_rebuild_requests()

    def _subscribe_to_rebuild_requests(self):
        """Subscribes to the UI Rebuild topic to allow live updates from external editors."""
        if not self.subscriber_router or not self.json_filepath:
            return
            
        rebuild_topic = "OPEN-AIR/System/Control/UI/Rebuild"
        
        def _handle_rebuild_request(message):
            # ⚡ ZERO EXCEPTION: Structural validation before processing
            payload = message.payload
            if not payload: return
            
            # Simple check for JSON-like structure
            if not (payload.startswith(b"{") or payload.startswith("{")):
                return

            data = orjson.loads(payload)
            target_path = data.get("path")
            new_config = data.get("config")
            
            # Check if this builder instance is for the requested file
            if target_path and str(Path(target_path).resolve()) == str(self.json_filepath.resolve()):
                matrix_log("ui", "gui_shell", "_handle_rebuild_request", f"♻️ MQTT: Rebuild request received for '{self.tab_name}'. Injecting new config...", "INFO")
                
                # 1. Update config data
                if new_config:
                    self.config_data = new_config
                
                # 2. Trigger rebuild (GuiRebuilderMixin)
                if hasattr(self, "_rebuild_gui"):
                    # Use self.after to ensure we run on the main Tkinter thread
                    self.after(0, self._rebuild_gui)


        # Correct method name is subscribe_to_topic
        self.subscriber_router.subscribe_to_topic(rebuild_topic, _handle_rebuild_request)

    # Publishes the entire JSON configuration data to the base MQTT topic.
    # This allows other parts of the system to be aware of the GUI's structure and configuration.
    # Inputs:
    #     json_data (dict): The JSON data to be published.
    # Outputs:
    #     None.
    def _publish_json_to_topic(self, json_data):
        """Publishes the entire JSON data to the base topic."""
        # ⚡ ICE: User requested to stop GUI from announcing itself
        #     payload = {
        #         "value": json_data,
        #         "source": "GUI-INIT",
        #         "timestamp": time.time(),
        #         "GUID": self.state_mirror_engine.GUID,
        #     }
        #     # ⚡ CONSISTENCY: Use engine to calculate absolute topic
        #     full_topic = self.state_mirror_engine.calculate_topic("", self.base_mqtt_topic_from_path)
        #     self.state_mirror_engine.publish_command(full_topic, orjson.dumps(payload).decode())
        pass

    def _publish_initial_widget_states(self, config_data):
        """
        Forces an initial MQTT announcement for all registered widgets in this builder.
        Ensures the broker/SNMP bridge has the complete state on load.
        """
        if self.state_mirror_engine:
            self.state_mirror_engine.announce_all_widgets()

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
                # ⚡ CONSISTENCY: Use engine to calculate absolute topic
                topic = self.state_mirror_engine.calculate_topic(widget_name, self.base_mqtt_topic_from_path)
                payload = {
                    "value": value,
                    "src": "gui",
                    "timestamp": time.time(),
                    "GUID": self.state_mirror_engine.GUID,
                }
                self.state_mirror_engine.publish_command(topic, orjson.dumps(payload).decode())