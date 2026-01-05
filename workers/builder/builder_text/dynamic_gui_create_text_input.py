# workers/builder/dynamic_gui_create_text_input.py

import tkinter as tk
from tkinter import ttk
from managers.configini.config_reader import Config                                                                          
from workers.mqtt.mqtt_topic_utils import get_topic # Import get_topic

app_constants = Config.get_instance() # Get the singleton instance      
from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args 
import os

class TextInputCreatorMixin:
    def _create_text_input(self, parent_widget, config_data, **kwargs): # Updated signature
        """Creates a text input widget."""
        current_function_name = "_create_text_input"
        
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
                message=f"🔬⚡️ Entering '{current_function_name}' to forge a text input field for '{label}'.",
**_get_log_args()
            )

        frame = ttk.Frame(parent_widget) # Use parent_widget here

        if label:
            ttk.Label(frame, text=label).pack(side=tk.LEFT, padx=(0, 10))

        try:
            text_var = tk.StringVar()
            text_var.set(config.get("value_default", ""))
            
            entry = ttk.Entry(
                frame,
                textvariable=text_var
            )
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

            def _on_text_change(*args):
                try:
                    if app_constants.global_settings['debug_enabled']:
                        debug_logger(message=f"Text changed for {label}: {text_var.get()}", file=os.path.basename(__file__), function="_on_text_change")
                    state_mirror_engine.broadcast_gui_change_to_mqtt(path)
                except Exception as e:
                    if app_constants.global_settings['debug_enabled']:
                        debug_logger(message=f"🔴 ERROR in _on_text_change: {e}", file=os.path.basename(__file__), function="_on_text_change")

            text_var.trace_add("write", _on_text_change) # Use trace_add for consistency

            if path:
                widget_id = path
                state_mirror_engine.register_widget(widget_id, text_var, base_mqtt_topic_from_path, config)
                
                # Subscribe to this widget's topic to receive updates
                topic = get_topic("OPEN-AIR", self.state_mirror_engine.base_topic, widget_id)
                self.subscriber_router.subscribe_to_topic(topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui)

                if app_constants.global_settings['debug_enabled']:
                    debug_logger(
                        message=f"🔬 Widget '{label}' ({path}) registered with StateMirrorEngine (StringVar: {text_var.get()}).",
                        **_get_log_args()
                    )
                # Initialize state from cache or broadcast
                state_mirror_engine.initialize_widget_state(path)
            
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"✅ SUCCESS! The text input '{label}' has been successfully forged!",
                    file=os.path.basename(__file__),
                    version=app_constants.CURRENT_VERSION,
                    function=f"{self.__class__.__name__}.{current_function_name}"
                    


                )
            return frame
        except Exception as e:
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"❌ The text input '{label}' has disintegrated! Error: {e}",
                    file=os.path.basename(__file__),
                    version=app_constants.CURRENT_VERSION,
                    function=current_function_name
                )
            return None