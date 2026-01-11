# builder_text/dynamic_gui_create_gui_dropdown_option.py
#
# This file provides the GuiDropdownOptionCreatorMixin class for creating dropdown (Combobox) widgets in the GUI.
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
# Version 20260110.2115.2

import os
import tkinter as tk
from tkinter import ttk
import inspect
from decimal import Decimal, InvalidOperation 

# --- Module Imports ---
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config
from workers.mqtt.mqtt_topic_utils import get_topic

app_constants = Config.get_instance()  # Get the singleton instance
# --- Global Scope Variables ---
current_file = f"{os.path.basename(__file__)}"
current_version = "20260110.2115.2"
current_version_hash = 4321098765 # Calculated hash

# --- Constants ---
DEFAULT_PAD_X = 5
DEFAULT_PAD_Y = 2


class GuiDropdownOptionCreatorMixin:
    """
    A mixin class that provides the functionality for creating a
    dropdown (Combobox) widget.
    """

    # Creates a dropdown menu (Combobox) widget for selecting from a list of options.
    # This method sets up a Tkinter Combobox, populates it with options from the configuration,
    # manages its selected value via a StringVar, and synchronizes its state via MQTT.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): Configuration for the dropdown widget.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     ttk.Frame: The created frame containing the dropdown widget, or None on failure.
    def _create_gui_dropdown_option(
        self, parent_widget, config_data, **kwargs
    ): 
        """Creates a dropdown menu for multiple choice options."""
        current_function_name = inspect.currentframe().f_code.co_name

        # Extract only widget-specific config from config_data
        label = config_data.get("label")
        config = config_data  # config_data is the config
        path = config_data.get("path")

        # Access global context directly from self
        state_mirror_engine = self.state_mirror_engine
        subscriber_router = self.subscriber_router
        base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")

        # 1. Debug Entry
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🧪 Great Scott! Configuring Dropdown for '{label}'...",
                **_get_log_args(),
            )

        try:
            sub_frame = ttk.Frame(parent_widget) 

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
                options_map = {} 

            # Helper to get the best display label
            def get_display_label(opt_data, default_key):
                # Prioritize 'label_active', then 'label', then fallback to key
                return opt_data.get("label_active") or opt_data.get("label") or default_key

            # Try to convert values to Decimal for numerical sorting, fall back to string sorting.
            sorted_options = sorted(
                options_map.items(),
                key=lambda item: str(item[1].get("value", item[0])),
            )

            # Populate the dropdown with labels and map them to values
            # FIX: Use get_display_label to fetch 'label_active' properly!
            option_labels = [
                get_display_label(opt, key) for key, opt in sorted_options
            ]
            option_values = [opt.get("value", key) for key, opt in sorted_options]

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🧐 Options loaded for '{label}': {option_labels}",
                    **_get_log_args(),
                )

            # Determine initial selection:
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
                        # FIX: Use get_display_label here too
                        initial_displayed_text = get_display_label(opt, key)
                        break
            
            displayed_text_var = tk.StringVar(value=initial_displayed_text)

            # Store the currently selected key for transmit_command (needed for path building)
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
                        # FIX: Use get_display_label here too
                        found_label = get_display_label(opt, key)
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
                    
                    # Reverse lookup: Find key based on displayed label
                    selected_key = next(
                        (
                            key
                            for key, opt in options_map.items()
                            # FIX: Match against get_display_label
                            if get_display_label(opt, key) == selected_label
                        ),
                        None,
                    )
                    
                    if selected_key:
                        selected_value = options_map.get(selected_key, {}).get("value", selected_key)

                        # Update the StringVar directly. This will trigger the trace.
                        if selected_value_var.get() != str(selected_value):  
                            selected_value_var.set(selected_value)

                        if app_constants.global_settings["debug_enabled"]:
                            debug_logger(
                                message=f"GUI ACTION: Publishing to '{path}' with value '{selected_value}' (Label: {selected_label})",
                                **_get_log_args(),
                            )
                        # Broadcast the change
                        self.state_mirror_engine.broadcast_gui_change_to_mqtt(path)
                        self._current_selected_key_for_path = selected_key 
                    else:
                        debug_logger(message=f"⚠️ Warning: Could not find key for label '{selected_label}'")

                except ValueError:
                    debug_logger(message="❌ Invalid selection in dropdown.")

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
                        message=f"🔬 Widget '{label}' ({path}) registered. State: {selected_value_var.get()}",
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