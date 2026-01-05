# workers/builder/dynamic_gui_create_value_box.py
#
# This file (dynamic_gui_create_value_box.py) provides the ValueBoxCreatorMixin class for creating editable text box widgets in the GUI.
# A complete and comprehensive pre-amble that describes the file and the functions within.
# The purpose is to provide clear documentation and versioning.
#
# The hash calculation drops the leading zero from the hour (e.g., 08 -> 8)
# As the current hour is 20, no change is needed.

Current_Date = 20251213  ##Update on the day the change was made
Current_Time = 120000  ## update at the time it was edited and compiled
Current_iteration = 44 ## a running version number - incriments by one each time 

current_version = f"{Current_Date}.{Current_Time}.{Current_iteration}"
current_version_hash = (Current_Date * Current_Time * Current_iteration)


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


import os
import tkinter as tk
from tkinter import ttk
import inspect

# --- Module Imports ---
from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config                                                                          

app_constants = Config.get_instance() # Get the singleton instance      
from workers.handlers.widget_event_binder import bind_variable_trace
from workers.mqtt.mqtt_topic_utils import get_topic

# --- Global Scope Variables ---
current_file = f"{os.path.basename(__file__)}"

# --- Constants ---
DEFAULT_PAD_X = 5
DEFAULT_PAD_Y = 2

class ValueBoxCreatorMixin:
    """
    A mixin class that provides the functionality for creating an
    editable text box widget.
    """
    def _create_value_box(self, parent_widget, config_data): # Updated signature
        # Creates an editable text box (_Value).
        current_function_name = inspect.currentframe().f_code.co_name

        # Extract arguments from config_data
        label = config_data.get("label_active")
        config = config_data # config_data is the config
        path = config_data.get("path")
        base_mqtt_topic_from_path = config_data.get("base_mqtt_topic_from_path")
        state_mirror_engine = config_data.get("state_mirror_engine")
        subscriber_router = config_data.get("subscriber_router")

        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"🔬⚡️ Entering '{current_function_name}' to brew a value box for '{label}'.",
              **_get_log_args()
            )

        try:
            sub_frame = ttk.Frame(parent_widget) # Use parent_widget here

            label_widget = ttk.Label(sub_frame, text=f"{label}:")
            label_widget.pack(side=tk.LEFT, padx=(DEFAULT_PAD_X, DEFAULT_PAD_X))

            entry_value = tk.StringVar(value=config.get('value', ''))
            entry = ttk.Entry(sub_frame, textvariable=entry_value, style="Custom.TEntry")
            entry.pack(side=tk.LEFT, padx=DEFAULT_PAD_X)

            if config.get('units'):
                units_label = ttk.Label(sub_frame, text=config['units'])
                units_label.pack(side=tk.LEFT, padx=(0, DEFAULT_PAD_X))

            if path:
                self.topic_widgets[path] = entry
                
                # --- New MQTT Wiring ---
                if state_mirror_engine and subscriber_router: # Now explicitly passed
                    widget_id = path
                    
                    # 1. Register widget
                    state_mirror_engine.register_widget(widget_id, entry_value, base_mqtt_topic_from_path, config)

                    # 2. Bind variable trace for outgoing messages
                    callback = lambda *args: state_mirror_engine.broadcast_gui_change_to_mqtt(widget_id) # Added *args
                    bind_variable_trace(entry_value, callback)

                    # 3. Subscribe to topic for incoming messages
                    topic = get_topic("OPEN-AIR", base_mqtt_topic_from_path, widget_id)
                    subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
                    
                    # 4. Initialize state from cache or broadcast
                    state_mirror_engine.initialize_widget_state(widget_id)


            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"✅ SUCCESS! The value box '{label}' has been perfectly crafted!",
                    **_get_log_args()
                )
            return sub_frame

        except Exception as e:
            debug_logger(message=f"❌ Error in {current_function_name} for '{label}': {e}")
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"💥 KABOOM! The value box for '{label}' has spectacularly failed! Error: {e}",
                    **_get_log_args()
                )
            return None