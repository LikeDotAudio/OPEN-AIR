# workers/builder/dynamic_gui_create_fader.py

import tkinter as tk
from tkinter import ttk
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
import os
from workers.mqtt.mqtt_topic_utils import get_topic


class FaderCreatorMixin:
    def _create_fader(self, parent_widget, config_data, **kwargs):  # Updated signature
        """Creates a fader widget."""
        current_function_name = "_create_fader"

        # Extract only widget-specific config from config_data
        label = config_data.get("label_active")
        config = config_data  # config_data is the config
        path = config_data.get("path")

        # Access global context directly from self
        state_mirror_engine = self.state_mirror_engine
        subscriber_router = self.subscriber_router
        base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")


        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔬⚡️ Entering '{current_function_name}' to sculpt a fader for '{label}'.",
                **_get_log_args(),
            )

        frame = ttk.Frame(parent_widget)  # Use parent_widget here

        if label:
            ttk.Label(frame, text=label).pack(side=tk.TOP, pady=(0, 5))

        try:
            orient = config.get("orientation", "vertical")
            value_default = float(config.get("value_default", 0))  # Ensure float
            fader_value_var = tk.DoubleVar(value=value_default)

            scale = ttk.Scale(
                frame,
                from_=config.get("min", 0),
                to=config.get("max", 100),
                orient=orient,
                variable=fader_value_var,  # Bind the StringVar to the scale
                length=130,  # Set fixed width to 130 pixels
            )

            if orient == "vertical":
                scale.pack(side=tk.LEFT, fill=tk.Y, expand=True)
            else:
                scale.pack(side=tk.TOP, fill=tk.X, expand=True)

            value_label = ttk.Label(frame, text=f"{fader_value_var.get():.2f}")
            if orient == "vertical":
                value_label.pack(side=tk.BOTTOM, pady=(5, 0))
            else:
                value_label.pack(side=tk.RIGHT, padx=(10, 0))

            def update_fader_visuals(*args):
                current_fader_val = fader_value_var.get()
                value_label.config(text=f"{current_fader_val:.2f}")
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"⚡ fluxing... Fader '{label}' updated visually to {current_fader_val} from MQTT.",
                        **_get_log_args(),
                    )

            fader_value_var.trace_add("write", update_fader_visuals)

            # Initial update of the label
            update_fader_visuals()

            def _on_scale_change(*args):
                # This is triggered by user interaction AND tk_var.set
                # Only publish if it's a user interaction (not an MQTT sync)
                # The _silent_update flag in StateMirrorEngine handles the suppression

                # Publish the value via MQTT
                self.state_mirror_engine.broadcast_gui_change_to_mqtt(path)

            scale.config(command=_on_scale_change)  # Bind command to the trace

            if path:
                widget_id = path
                # Register the widget with the StateMirrorEngine for MQTT updates
                self.state_mirror_engine.register_widget(
                    widget_id, fader_value_var, base_mqtt_topic_from_path, config
                )

                # Subscribe to this widget's topic to receive updates
                topic = self.state_mirror_engine.get_widget_topic(widget_id)
                if topic:
                    self.subscriber_router.subscribe_to_topic(
                        topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui
                    )

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"🔬 Widget '{label}' ({path}) registered with StateMirrorEngine (DoubleVar: {fader_value_var.get()}).",
                        **_get_log_args(),
                    )
                # Initialize state from cache or broadcast
                state_mirror_engine.initialize_widget_state(path)

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"✅ SUCCESS! The fader '{label}' is now sliding into existence!",
                    **_get_log_args(),
                )
            return frame
        except Exception as e:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌ The fader for '{label}' has gone off the rails! Error: {e}",
                    file=os.path.basename(__file__),
                    version=app_constants.CURRENT_VERSION,
                    function=current_function_name,
                )
            return None
