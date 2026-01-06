# workers/builder/dynamic_gui_create_web_link.py

import tkinter as tk
from tkinter import ttk
import webbrowser
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
import os


class WebLinkCreatorMixin:
    def _create_web_link(
        self, parent_widget, config_data, **kwargs
    ):  # Updated signature
        """Creates a web link widget."""
        current_function_name = "_create_web_link"

        # Extract arguments from config_data
        label = config_data.get("label_active")
        config = config_data  # config_data is the config
        # path = config_data.get("path") # Not directly used in this widget for MQTT
        # base_mqtt_topic_from_path = config_data.get("base_mqtt_topic_from_path")
        # state_mirror_engine = config_data.get("state_mirror_engine")
        # subscriber_router = config_data.get("subscriber_router")

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔬⚡️ Entering '{current_function_name}' to open a portal (web link) for '{label}'.",
                **_get_log_args(),
            )

        frame = ttk.Frame(parent_widget)  # Use parent_widget here

        try:
            url = config.get("url", "#")
            link_label = ttk.Label(frame, text=label, foreground="blue", cursor="hand2")
            link_label.pack(side=tk.LEFT)

            def _open_url(event):
                try:
                    if app_constants.global_settings["debug_enabled"]:
                        debug_logger(
                            message=f"Opening URL: {url}",
                            file=os.path.basename(__file__),
                            function="_open_url",
                        )
                    webbrowser.open_new(url)
                except Exception as e:
                    if app_constants.global_settings["debug_enabled"]:
                        debug_logger(
                            message=f"❌ ERROR opening URL: {e}",
                            file=os.path.basename(__file__),
                            function="_open_url",
                        )

            link_label.bind("<Button-1>", _open_url)

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"✅ SUCCESS! The portal to '{label}' has been opened!",
                    file=os.path.basename(__file__),
                    version=app_constants.CURRENT_VERSION,
                    function=f"{self.__class__.__name__}.{current_function_name}",
                )
            return frame
        except Exception as e:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌ The web link for '{label}' has collapsed into a singularity! Error: {e}",
                    file=os.path.basename(__file__),
                    version=app_constants.CURRENT_VERSION,
                    function=current_function_name,
                )
            return None
