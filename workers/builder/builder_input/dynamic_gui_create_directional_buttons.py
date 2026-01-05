# workers/builder/dynamic_gui_create_directional_buttons.py

import tkinter as tk
from tkinter import ttk
from managers.configini.config_reader import Config                                                                          
app_constants = Config.get_instance() # Get the singleton instance      
from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args 
import os
from workers.mqtt.mqtt_topic_utils import get_topic # Import get_topic

import orjson # Imported here for payload construction
import time # Imported for timestamp

class DirectionalButtonsCreatorMixin:
    def _create_directional_buttons(self, parent_widget, config_data, **kwargs): # Updated signature
        """Creates a set of directional buttons (up, down, left, right)."""
        current_function_name = "_create_directional_buttons"
        
        # Extract only widget-specific config from config_data
        label = config_data.get("label_active")
        config = config_data # config_data is the config
        path = config_data.get("path")
        
        # Access global context directly from self
        state_mirror_engine = self.state_mirror_engine
        subscriber_router = self.subscriber_router
        base_mqtt_topic_from_path = self.state_mirror_engine.base_topic if self.state_mirror_engine else ""

        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"🔬⚡️ Entering '{current_function_name}' to chart the course for directional buttons for '{label}'.",
**_get_log_args()
            )

        frame = ttk.Frame(parent_widget) # Use parent_widget here

        if label:
            ttk.Label(frame, text=label).grid(row=0, column=1, pady=(0, 5))

        # Create buttons
        up_button = ttk.Button(frame, text="⬆")
        down_button = ttk.Button(frame, text="⬇")
        left_button = ttk.Button(frame, text="⬅")
        right_button = ttk.Button(frame, text="➡")

        up_button.grid(row=1, column=1)
        left_button.grid(row=2, column=0)
        right_button.grid(row=2, column=2)
        down_button.grid(row=3, column=1)

        import orjson # Imported here for payload construction
        import time # Imported for timestamp

        # Commands (these would typically publish MQTT messages)
        def _publish_command(action):
            action_path = f"{path}/{action}"
            topic = get_topic("OPEN-AIR", self.state_mirror_engine.base_topic, action_path)
            payload_data = {
                "val": True,
                "src": "gui",
                "ts": time.time(),
                "GUID": self.state_mirror_engine.GUID
            }
            self.state_mirror_engine.publish_command(topic, orjson.dumps(payload_data))
            if app_constants.global_settings['debug_enabled']:
                debug_logger(message=f"Published MQTT command: {topic} val: {True}", **_get_log_args())


        def _move_up():
            if app_constants.global_settings['debug_enabled']:
                debug_logger(message=f"Move Up for {path}", file=os.path.basename(__file__), function="_move_up")
            _publish_command("up")

        def _move_down():
            if app_constants.global_settings['debug_enabled']:
                debug_logger(message=f"Move Down for {path}", file=os.path.basename(__file__), function="_move_down")
            _publish_command("down")

        def _move_left():
            if app_constants.global_settings['debug_enabled']:
                debug_logger(message=f"Move Left for {path}", file=os.path.basename(__file__), function="_move_left")
            _publish_command("left")

        def _move_right():
            if app_constants.global_settings['debug_enabled']:
                debug_logger(message=f"Move Right for {path}", file=os.path.basename(__file__), function="_move_right")
            _publish_command("right")

        up_button.config(command=_move_up)
        down_button.config(command=_move_down)
        left_button.config(command=_move_left)
        right_button.config(command=_move_right)

        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"✅ SUCCESS! The directional buttons for '{label}' are pointing the way!",
**_get_log_args()
                


            )
        return frame