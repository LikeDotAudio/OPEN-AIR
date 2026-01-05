# workers/builder/dynamic_gui_create_progress_bar.py

import tkinter as tk
from tkinter import ttk
from managers.configini.config_reader import Config                                                                          

app_constants = Config.get_instance() # Get the singleton instance      
from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args
from workers.mqtt.mqtt_topic_utils import get_topic
import os
class ProgressBarCreatorMixin:
    def _create_progress_bar(self, parent_widget, config_data, **kwargs): # Updated signature
        """Creates a progress bar widget that is state-aware."""
        current_function_name = "_create_progress_bar"
        
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
                message=f"🔬⚡️ Entering '{current_function_name}' to construct a progress indicator for '{label}'.",
                **_get_log_args()
            )

        frame = ttk.Frame(parent_widget) # Use parent_widget here

        if label:
            ttk.Label(frame, text=label).pack(side=tk.LEFT, padx=(0, 10))

        try:
            min_val = float(config.get("min", 0))
            max_val = float(config.get("max", 100))
            value_default = float(config.get("value_default", min_val))
            units = config.get("units", "")

            progress_var = tk.DoubleVar(value=value_default)
            
            progressbar = ttk.Progressbar(
                frame,
                orient="horizontal",
                length=200,
                mode="determinate",
                maximum=max_val,
                variable=progress_var
            )
            progressbar.pack(side=tk.LEFT, fill=tk.X, expand=True)

            value_label = ttk.Label(frame, text=f"{progress_var.get()} {units}")
            value_label.pack(side=tk.LEFT, padx=(10, 0))

            def update_label(*args):
                """Updates the label next to the progress bar."""
                try:
                    current_value = progress_var.get()
                    value_label.config(text=f"{current_value:.1f} {units}")
                except Exception as e:
                    if app_constants.global_settings['debug_enabled']:
                        debug_logger(message=f"❌ ERROR in update_label for progress bar: {e}", **_get_log_args())

            progress_var.trace_add("write", update_label)
            update_label() # Initial update

            if path:
                widget_id = path
                state_mirror_engine.register_widget(widget_id, progress_var, base_mqtt_topic_from_path, config)
                
                # Subscribe to the topic for incoming messages
                from workers.mqtt.mqtt_topic_utils import get_topic
                topic = get_topic("OPEN-AIR", self.state_mirror_engine.base_topic, widget_id)
                self.subscriber_router.subscribe_to_topic(topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui)

                if app_constants.global_settings['debug_enabled']:
                    debug_logger(
                        message=f"🔬 Widget '{label}' ({path}) registered with StateMirrorEngine.",
                        **_get_log_args()
                    )
                # Initialize state from cache or broadcast
                state_mirror_engine.initialize_widget_state(path)

            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"✅ SUCCESS! The progress bar '{label}' has been successfully rendered!",
                    **_get_log_args()
                )
            return frame
        except Exception as e:
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"❌ The progress bar '{label}' has failed to materialize! Error: {e}",
                    **_get_log_args()
                )
            return None