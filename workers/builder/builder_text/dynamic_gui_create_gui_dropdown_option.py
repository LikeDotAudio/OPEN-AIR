# workers/builder/dynamic_gui_create_gui_dropdown_option.py
#
# This file (dynamic_gui_create_gui_dropdown_option.py) provides the GuiDropdownOptionCreatorMixin class for creating dropdown (Combobox) widgets in the GUI.
# A complete and comprehensive pre-amble that describes the file and the functions within.
# The purpose is to provide clear documentation and versioning.
#
# The hash calculation drops the leading zero from the hour (e.g., 08 -> 8)
# As the current hour is 20, no change is needed.

Current_Date = 20251213  ##Update on the day the change was made
Current_Time = 120000  ## update at the time it was edited and compiled
Current_iteration = 44  ## a running version number - incriments by one each time

current_version = f"{Current_Date}.{Current_Time}.{Current_iteration}"
current_version_hash = Current_Date * Current_Time * Current_iteration


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
from decimal import Decimal, InvalidOperation  # Add InvalidOperation

# --- Module Imports ---
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config
from workers.mqtt.mqtt_topic_utils import get_topic

app_constants = Config.get_instance()  # Get the singleton instance
# --- Global Scope Variables ---
current_file = f"{os.path.basename(__file__)}"

# --- Constants ---
DEFAULT_PAD_X = 5
DEFAULT_PAD_Y = 2


class GuiDropdownOptionCreatorMixin:
    """
    A mixin class that provides the functionality for creating a
    dropdown (Combobox) widget.
    """

    def _create_gui_dropdown_option(
        self, parent_widget, config_data, **kwargs
    ):  # Updated signature
        # Creates a dropdown menu for multiple choice options.
        current_function_name = inspect.currentframe().f_code.co_name

        # Extract only widget-specific config from config_data
        label = config_data.get("label_active")
        config = config_data  # config_data is the config
        path = config_data.get("path")

        # Access global context directly from self
        state_mirror_engine = self.state_mirror_engine
        subscriber_router = self.subscriber_router
        base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")

        try:
            sub_frame = ttk.Frame(parent_widget)  # Use parent_widget here

            # Label
            label_widget = ttk.Label(sub_frame, text=f"{label}:")
            label_widget.pack(side=tk.LEFT, padx=(DEFAULT_PAD_X, 0))

            options_map = config.get("options", {})
            # Ensure options_map is a dictionary
            if isinstance(options_map, list):
                debug_logger(
                    message=f"⚠️ WARNING: 'options' for '{label}' in config is a list, expected a dictionary. Falling back to empty dict.",
                    **_get_log_args(),
                )
                options_map = {}  # Fallback to empty dict to prevent crash

            # Use all options from options_map, as 'active' status is not consistently used
            # in current JSON structures like gui_amplitude.json.
            active_options = options_map

            # Try to convert values to Decimal for numerical sorting, fall back to string sorting.
            sorted_options = sorted(
                active_options.items(),
                key=lambda item: str(item[1].get("value", item[0])),
            )

            # Populate the dropdown with labels and map them to values
            option_labels = [
                opt.get("label_active", key) for key, opt in sorted_options
            ]
            option_values = [opt.get("value", key) for key, opt in sorted_options]

            # Determine initial selection:
            # 1. Use 'value_default' from config if provided
            # 2. Otherwise, use an option marked 'selected: true'
            # 3. Otherwise, default to the first available option.
            initial_value_from_config = config.get("value_default")

            initial_selected_value = None
            if initial_value_from_config is not None:
                initial_selected_value = initial_value_from_config
            else:
                initial_selected_option_entry = next(
                    (
                        opt
                        for key, opt in options_map.items()
                        if str(opt.get("selected", "no")).lower() in ["yes", "true"]
                    ),
                    None,
                )
                if initial_selected_option_entry:
                    initial_selected_value = initial_selected_option_entry.get("value")

            # If nothing is selected, and there are options, pick the first one
            if initial_selected_value is None and option_values:
                initial_selected_value = option_values[0]

            selected_value_var = tk.StringVar(value=initial_selected_value)

            # Set displayed_text_var based on the initial_selected_value
            initial_displayed_text = ""
            if initial_selected_value is not None:
                for key, opt in options_map.items():
                    if str(opt.get("value", key)) == str(initial_selected_value):
                        initial_displayed_text = opt.get("label_active", key)
                        break
            displayed_text_var = tk.StringVar(value=initial_displayed_text)

            # Store the currently selected key for transmit_command (needed for path building)
            # This is complex because 'path' refers to the dropdown itself, not an option
            # The 'on_select' needs to construct the path to the *selected option*.
            self._current_selected_key_for_path = None
            if initial_selected_value:
                self._current_selected_key_for_path = next(
                    (
                        k
                        for k, v in options_map.items()
                        if str(v.get("value", k)) == str(initial_selected_value)
                    ),
                    None,
                )

            def update_displayed_text_from_value_var(*args):
                """Callback for when selected_value_var changes (e.g., from MQTT)."""
                new_value = selected_value_var.get()
                found_label = ""
                for key, opt in options_map.items():
                    if str(opt.get("value", key)) == str(new_value):
                        found_label = opt.get("label_active", key)
                        break
                displayed_text_var.set(found_label)
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"⚡ fluxing... Dropdown '{label}' visually updated to '{found_label}' (value: {new_value}) from MQTT.",
                        **_get_log_args(),
                    )

            selected_value_var.trace_add("write", update_displayed_text_from_value_var)

            def on_select(event):
                try:
                    selected_label = displayed_text_var.get()
                    selected_key = next(
                        (
                            key
                            for key, opt in options_map.items()
                            if opt.get("label_active", key) == selected_label
                        ),
                        None,
                    )
                    selected_value = options_map.get(selected_key, {}).get(
                        "value", selected_key
                    )

                    # Only transmit if a valid selection was made and it changed
                    if selected_key:
                        # Update the StringVar directly. This will trigger the trace.
                        if selected_value_var.get() != str(
                            selected_value
                        ):  # Prevent unnecessary trace trigger
                            selected_value_var.set(selected_value)

                        # The 'AES70' and 'handler' from config imply the 'path' is the target for the value.
                        if app_constants.global_settings["debug_enabled"]:
                            debug_logger(
                                message=f"GUI ACTION: Publishing to '{path}' with value '{selected_value}'",
                                **_get_log_args(),
                            )
                        # Instead of self._transmit_command, directly broadcast the change
                        self.state_mirror_engine.broadcast_gui_change_to_mqtt(path)
                        self._current_selected_key_for_path = (
                            selected_key  # Update for consistency
                        )

                except ValueError:
                    debug_logger(message="❌ Invalid selection in dropdown.")

            # No longer hardcode style, rely on _apply_styles from DynamicGuiBuilder
            # Create a Combobox that uses the displayed_text_var for its text.
            dropdown = ttk.Combobox(
                sub_frame,
                textvariable=displayed_text_var,
                values=option_labels,
                state="readonly",
                style="BlackText.TCombobox",
            )

            dropdown.bind("<<ComboboxSelected>>", on_select)
            dropdown.pack(side=tk.LEFT, padx=DEFAULT_PAD_X)

            if path:
                widget_id = path
                # Register the StringVar with the StateMirrorEngine for MQTT updates
                state_mirror_engine.register_widget(
                    widget_id, selected_value_var, base_mqtt_topic_from_path, config
                )

                # Subscribe to this widget's topic to receive updates
                topic = get_topic(
                    self.state_mirror_engine.base_topic, base_mqtt_topic_from_path, widget_id
                )
                if topic:
                    self.subscriber_router.subscribe_to_topic(
                        topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui
                    )

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"🔬 Widget '{label}' ({path}) registered with StateMirrorEngine (StringVar: {selected_value_var.get()}).",
                        **_get_log_args(),
                    )
                # Broadcast initial state or load from cache
                state_mirror_engine.initialize_widget_state(path)
            return sub_frame

        except Exception as e:
            debug_logger(
                message=f"❌ Error in {current_function_name} for '{label}': {e}"
            )
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"💥 KABOOM! The dropdown for '{label}' has fallen into the abyss! Error: {e}",
                    **_get_log_args(),
                )
            return None
