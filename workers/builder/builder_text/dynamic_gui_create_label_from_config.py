# display/builder/dynamic_gui_create_label_from_config.py
#
# A mixin class for the DynamicGuiBuilder that handles creating a label from a config dictionary.
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
import inspect

# --- Module Imports ---
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

# --- Global Scope Variables ---
current_version = "20251127.000000.1"
current_version_hash = 20251127 * 0 * 1
current_file = f"{os.path.basename(__file__)}"


class LabelFromConfigCreatorMixin:
    """
    A mixin class that provides a wrapper for creating a label widget
    from a configuration dictionary.
    """

    def _create_label_from_config(
        self, parent_widget, config_data, **kwargs
    ):  # Updated signature
        # A wrapper for _create_label to match the factory function signature.
        # It calls the _create_label method (provided by LabelCreatorMixin).
        current_function_name = inspect.currentframe().f_code.co_name

        # Extract only widget-specific config from config_data
        label = config_data.get("label_active")  # Use label from config_data
        config = config_data  # config_data is the config
        path = config_data.get("path")

        # Access global context directly from self
        state_mirror_engine = self.state_mirror_engine
        subscriber_router = self.subscriber_router
        base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🟢️️️🟢 ➡️➡️ '{current_function_name}' to create label from config for '{label}'.",
                **_get_log_args(),
            )
        try:
            # Prepare a config dictionary for _create_label, which now also expects a config_data dict
            label_config = config_data.copy()
            label_config["parent_widget"] = (
                parent_widget  # Pass parent_widget through config for _create_label
            )
            label_config["label_active"] = label  # Ensure label is in config
            label_config["path"] = path
            label_config["base_mqtt_topic_from_path"] = (
                base_mqtt_topic_from_path  # Pass the derived base_mqtt_topic_from_path
            )
            label_config["state_mirror_engine"] = (
                state_mirror_engine  # Pass the derived state_mirror_engine
            )
            label_config["subscriber_router"] = (
                subscriber_router  # Pass the derived subscriber_router
            )

            result = self._create_label(
                parent_frame=parent_widget,
                label=label,
                value=config_data.get("value", ""),
                units=config_data.get("units"),
                path=path,
                base_mqtt_topic_from_path=base_mqtt_topic_from_path,
                state_mirror_engine=state_mirror_engine,
                subscriber_router=subscriber_router,
                config=config_data,
            )
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🟢️️️🟢 📤 '{current_function_name}'. Label from config '{label}' created.",
                    **_get_log_args(),
                )
            return result
        except Exception as e:
            debug_logger(
                message=f"❌ Error in {current_function_name} for '{label}': {e}"
            )
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🟢️️️🔴 Arrr, the code be capsized! Label from config creation has failed! The error be: {e}",
                    **_get_log_args(),
                )
            return None
