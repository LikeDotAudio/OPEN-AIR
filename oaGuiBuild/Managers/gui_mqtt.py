# core/gui_mqtt_manager.py
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
from pathlib import Path

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants_config = Config.get_instance()

from oaComMQTT.Methods.mqtt_topic_utils import get_topic, generate_topic_path_from_filepath
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
        
        # ⚡ REMOTE REBUILD: Listen for test requests from external editors
        self._subscribe_to_rebuild_requests()

    def _subscribe_to_rebuild_requests(self):
        """Subscribes to the UI Rebuild topic to allow live updates from external editors."""
        if not self.subscriber_router or not self.json_filepath:
            return
            
        rebuild_topic = "OPEN-AIR/System/Control/UI/Rebuild"
        
        def _handle_rebuild_request(msg):
            # ⚡ ZERO EXCEPTION: Structural validation before processing
            payload = msg.payload
            if not payload: return
            
            # Simple check for JSON-like structure
            if not (payload.startswith(b"{") or payload.startswith("{")):
                return

            data = orjson.loads(payload)
            target_path = data.get("path")
            new_config = data.get("config")
            
            # Check if this builder instance is for the requested file
            if target_path and str(Path(target_path).resolve()) == str(self.json_filepath.resolve()):
                if LOCAL_DEBUG: logger.info(f"♻️ MQTT: Rebuild request received for '{self.tab_name}'. Injecting new config...")
                
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
        # if self.state_mirror_engine and self.base_mqtt_topic_from_path:
        #     payload = {
        #         "val": json_data,
        #         "source": "GUI-INIT",
        #         "ts": time.time(),
        #         "GUID": self.state_mirror_engine.GUID,
        #     }
        #     # ⚡ CONSISTENCY: Use engine to calculate absolute topic
        #     full_topic = self.state_mirror_engine.calculate_topic("", self.base_mqtt_topic_from_path)
        #     if LOCAL_DEBUG: logger.debug(f"📡 MQTT: Auto-publishing config for '{self.tab_name}' to {full_topic}")
        #     self.state_mirror_engine.publish_command(full_topic, orjson.dumps(payload).decode())
        pass

    def _publish_initial_widget_states(self, config_data):
        """
        Recursively scans the config_data for widgets and publishes their initial values.
        This ensures all topics exist in the broker/SNMP bridge immediately on load.
        """
        # ⚡ ICE: User requested to stop initial widget state announcements
        # if not self.state_mirror_engine or not self.base_mqtt_topic_from_path:
        #     return
        # ... (implementation kept in comments if needed later)
        pass

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
                    "val": value,
                    "src": "gui",
                    "ts": time.time(),
                    "GUID": self.state_mirror_engine.GUID,
                }
                self.state_mirror_engine.publish_command(topic, orjson.dumps(payload).decode())
