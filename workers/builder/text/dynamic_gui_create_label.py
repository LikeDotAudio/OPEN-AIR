# display/builder/dynamic_gui_create_label.py
#
# A mixin class for the DynamicGuiBuilder that handles the creation of a label widget.
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
#
# Version 20251127.000000.1

import os
import tkinter as tk
from tkinter import ttk
import inspect

# --- Module Imports ---
from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config                                                                          
from workers.mqtt.mqtt_topic_utils import get_topic

app_constants = Config.get_instance() # Get the singleton instance      
from workers.handlers.widget_event_binder import bind_variable_trace

current_version = "20251127.000000.1"
current_version_hash = (20251127 * 0 * 1)
current_file = f"{os.path.basename(__file__)}"

# --- Constants ---
# These are local to this module but should match the main builder's constants.
DEFAULT_PAD_X = 5
DEFAULT_PAD_Y = 2

class LabelCreatorMixin:
    """
    A mixin class that provides the functionality for creating a label widget.
    """
    def _create_label(self, parent_frame, label, value, units=None, path=None, base_mqtt_topic_from_path=None, state_mirror_engine=None, subscriber_router=None, config=None):

        current_function_name = inspect.currentframe().f_code.co_name
        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"🔬⚡️ Entering '{current_function_name}' to concoct a new label: '{label}'.",
              **_get_log_args()
            )
        try:
            sub_frame = ttk.Frame(parent_frame)
            
            label_text = f"{label}: {value}"
            if units:
                label_text += f" {units}"

            label_var = tk.StringVar(value=label_text)
            label_widget = ttk.Label(sub_frame, textvariable=label_var)
            label_widget.pack(side=tk.LEFT, padx=(DEFAULT_PAD_X, DEFAULT_PAD_X))

            if path:
                self.topic_widgets[path] = label_widget
                
                # --- New MQTT Wiring ---
                if state_mirror_engine and subscriber_router: # Now explicitly passed
                    widget_id = path
                    
                    # 1. Register widget
                    state_mirror_engine.register_widget(widget_id, label_var, base_mqtt_topic_from_path, config)

                    # 2. Subscribe to topic for incoming messages
                    topic = get_topic("OPEN-AIR", base_mqtt_topic_from_path, widget_id)
                    subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)

                    # 3. Bind variable trace for outgoing messages
                    callback = lambda *args: state_mirror_engine.broadcast_gui_change_to_mqtt(widget_id) # Added *args
                    bind_variable_trace(label_var, callback)

                    # 4. Initialize state from cache or broadcast
                    state_mirror_engine.initialize_widget_state(widget_id)

            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"✅ SUCCESS! The label '{label}' has been successfully synthesized!",
                    **_get_log_args()
                )
            return sub_frame

        except Exception as e:
            debug_logger(message=f"❌ Error in {current_function_name} for '{label}': {e}")
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"💥 KABOOM! The label creation for '{label}' has exploded! Error: {e}",
                    **_get_log_args()
                )
            return None