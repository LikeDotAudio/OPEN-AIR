# builder_text/dynamic_gui_create_gui_listbox.py
#
# This file provides the GuiListboxCreatorMixin class for dynamically creating Listbox widgets in the GUI.
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
# Version 20250821.200641.1

import tkinter as tk
from tkinter import ttk
import os
import inspect
from decimal import Decimal, InvalidOperation
import time
from workers.mqtt.mqtt_subscriber_router import (
    MqttSubscriberRouter,
)  # Import MqttSubscriberRouter
from workers.mqtt.mqtt_topic_utils import (
    get_topic,
    TOPIC_DELIMITER,
)  # Import get_topic and TOPIC_DELIMITER

# --- Module Imports ---
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

# --- Global Scope Variables ---
current_file = f"{os.path.basename(__file__)}"

# --- Constants ---
DEFAULT_PAD_X = 5
DEFAULT_PAD_Y = 2


class GuiListboxCreatorMixin:
    """
    A mixin class that provides the functionality for creating a
    Listbox widget.
    """

    # Creates a Listbox widget for selecting from a list of options.
    # This method sets up a Tkinter Listbox with a scrollbar, populates it with options
    # from the configuration, handles selection events, and integrates with the state
    # management engine for MQTT synchronization, including dynamic updates to options.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): Configuration for the listbox widget.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     ttk.Frame: The created frame containing the listbox widget, or None on failure.
    def _create_gui_listbox(
        self, parent_widget, config_data, **kwargs
    ):  # Updated signature
        """Creates a listbox menu for multiple choice options."""
        current_function_name = inspect.currentframe().f_code.co_name

        # Extract widget-specific config from config_data
        label = config_data.get("label_active")  # Use label for this widget
        config = config_data  # config_data is the config
        path = config_data.get("path")  # Path for this widget

        # Access global context directly from self
        state_mirror_engine = self.state_mirror_engine
        subscriber_router = self.subscriber_router
        base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔬⚡️ Entering '{current_function_name}' to materialize a listbox for '{label}'.",
                **_get_log_args(),
            )

        try:
            sub_frame = ttk.Frame(
                parent_widget, width=200, height=150
            )  # Use parent_widget here
            sub_frame.pack_propagate(False)

            sub_frame.grid_rowconfigure(1, weight=1)
            sub_frame.grid_columnconfigure(0, weight=1)

            label_widget = ttk.Label(sub_frame, text=label)
            label_widget.grid(row=0, column=0, sticky="w", padx=DEFAULT_PAD_X, pady=2)

            listbox_frame = ttk.Frame(sub_frame)
            listbox_frame.grid(row=1, column=0, sticky="nsew")

            listbox_frame.grid_rowconfigure(0, weight=1)
            listbox_frame.grid_columnconfigure(0, weight=1)

            scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL)
            listbox = tk.Listbox(
                listbox_frame,
                yscrollcommand=scrollbar.set,
                exportselection=False,
                selectmode=tk.SINGLE,
                height=5,
                width=30,
            )

            scrollbar.config(command=listbox.yview)
            scrollbar.grid(row=0, column=1, sticky="ns")
            listbox.grid(row=0, column=0, sticky="nsew")

            self.options_map = config.get("options", {})  # Stored as instance variable
            self.listbox = listbox  # Stored as instance variable
            self.selected_option_var = tk.StringVar(
                sub_frame
            )  # Stored as instance variable
            # self.listbox_path = path # Removed as it's not needed as a self attribute

            # Store widget instance for debugging/reference
            self._listbox_widget_instance = listbox

            # --- MQTT Subscription for dynamic updates ---
            if self.subscriber_router and self.state_mirror_engine:
                wildcard_option_topic = get_topic(
                    self.state_mirror_engine.base_topic,
                    base_mqtt_topic_from_path,
                    path,
                    "options",
                    "#",
                )
                # Pass necessary context to the instance method
                self.subscriber_router.subscribe_to_topic(
                    topic_filter=wildcard_option_topic,
                    callback_func=lambda t, p, wp=path, bmt=base_mqtt_topic_from_path: self._on_option_mqtt_update_instance(
                        t, p, wp, bmt
                    ),  # Use instance method as callback
                )
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"🔬 Subscribed listbox '{label}' to MQTT topic: {wildcard_option_topic}",
                        **_get_log_args(),
                    )

            # Initial display build
            self._rebuild_listbox_display_instance(label)

            def update_listbox_from_var(*args):
                new_selection_label = self.selected_option_var.get()
                if new_selection_label:
                    # Update internal options_map for 'selected' status based on StringVar
                    found_key = None
                    for key, opt in self.options_map.items():
                        if opt.get("label_active") == new_selection_label:
                            found_key = key
                            self.options_map[key]["selected"] = "true"
                        else:
                            self.options_map[key]["selected"] = "false"

                    if new_selection_label in self.listbox.get(0, tk.END):
                        idx = self.listbox.get(0, tk.END).index(new_selection_label)
                        self.listbox.select_clear(
                            0, tk.END
                        )  # Clear previous selections
                        self.listbox.select_set(idx)
                        self.listbox.see(idx)
                        if app_constants.global_settings["debug_enabled"]:
                            debug_logger(
                                message=f"⚡ fluxing... Listbox '{label}' updated visually to '{new_selection_label}' from StringVar.",
                                **_get_log_args(),
                            )
                elif (
                    new_selection_label == ""
                ):  # Handle case where selection is cleared
                    for key, opt in self.options_map.items():
                        self.options_map[key]["selected"] = "false"
                    self.listbox.select_clear(0, tk.END)

            self.selected_option_var.trace_add("write", update_listbox_from_var)

            def on_select(event):
                widget = event.widget
                selection_indices = widget.curselection()
                if not selection_indices:
                    return

                selected_index = selection_indices[0]
                selected_label = widget.get(selected_index)

                try:
                    selected_key = next(
                        (
                            key
                            for key, opt in self.options_map.items()
                            if opt.get("label_active", key) == selected_label
                        ),
                        None,
                    )

                    if selected_key:
                        # Iterate over all options to enforce single selection
                        for key, opt in self.options_map.items():
                            is_selected = key == selected_key
                            topic_path = get_topic(
                                self.state_mirror_engine.base_topic,
                                base_mqtt_topic_from_path,
                                path,
                                "options",
                                key,
                                "selected",
                            )
                            payload = orjson.dumps(
                                {"val": is_selected, "ts": time.time()}
                            )
                            self.state_mirror_engine.publish_command(
                                topic_path, payload
                            )

                        self.selected_option_var.set(selected_label)  # Update the GUI

                        if app_constants.global_settings["debug_enabled"]:
                            debug_logger(
                                message=f"GUI ACTION: Publishing selection for '{selected_key}' to path '{path}'.",
                                **_get_log_args(),
                            )
                except (ValueError, StopIteration):
                    debug_logger(message="❌ Invalid selection in listbox.")

            listbox.bind("<<ListboxSelect>>", on_select)

            if path:
                widget_id = path
                # Register the StringVar with the StateMirrorEngine for MQTT updates
                state_mirror_engine.register_widget(
                    widget_id,
                    self.selected_option_var,
                    self.state_mirror_engine.base_topic,
                    config,
                )

                # Subscribe to this widget's topic to receive updates for its selected value
                topic = get_topic(
                    self.state_mirror_engine.base_topic, base_mqtt_topic_from_path, widget_id
                )
                if topic:
                    self.subscriber_router.subscribe_to_topic(
                        topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui
                    )

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"🔬 Widget '{label}' ({path}) registered with StateMirrorEngine (StringVar: {self.selected_option_var.get()}).",
                        **_get_log_args(),
                    )

                # Add trace for broadcasting the overall selected option
                callback = (
                    lambda *args: state_mirror_engine.broadcast_gui_change_to_mqtt(path)
                )
                self.selected_option_var.trace_add("write", callback)

                # Initialize state of the selected_option_var from cache or broadcast
                state_mirror_engine.initialize_widget_state(path)

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"✅ SUCCESS! The listbox '{label}' has been successfully generated!",
                    **_get_log_args(),
                )
            return sub_frame

        except Exception as e:
            debug_logger(
                message=f"❌ Error in {current_function_name} for '{label}': {e}"
            )
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"💥 KABOOM! The listbox for '{label}' has vanished into a different dimension! Error: {e}",
                    **_get_log_args(),
                )
            return None

    # Rebuilds the visual display of the listbox based on the current options map.
    # This method clears existing items in the listbox and repopulates it with active options,
    # maintaining the current selection if it is still valid.
    # Inputs:
    #     label (str): The label associated with the listbox (for logging purposes).
    # Outputs:
    #     None.
    def _rebuild_listbox_display_instance(self, label):
        lb = self.listbox
        cfg = {
            "options": self.options_map
        }  # Create a dummy config for rebuild function
        current_selection_label = self.selected_option_var.get()

        lb.delete(0, tk.END)
        active_options = {
            k: v
            for k, v in self.options_map.items()
            if str(v.get("active", "false")).lower() in ["true", "yes"]
        }

        def sort_key(item):
            value = item[1].get("value")
            return str(value)

        sorted_options = sorted(active_options.items(), key=sort_key)

        for key, opt in sorted_options:
            lb.insert(tk.END, opt.get("label_active", key))
            # Check against the *current* selection variable, not the initial one
            if opt.get("label_active", key) == current_selection_label:
                idx = lb.get(0, tk.END).index(current_selection_label)
                lb.select_set(idx)
                lb.see(idx)

        # If there was a selection previously and it's no longer active, clear the StringVar
        if current_selection_label and not any(
            opt.get("label_active", key) == current_selection_label
            and str(opt.get("active", "false")).lower() in ["true", "yes"]
            for opt in self.options_map.values()
        ):
            self.selected_option_var.set("")

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"⚡ Listbox '{label}' display rebuilt.", **_get_log_args()
            )

    # Callback function for updating listbox options via incoming MQTT messages.
    # This method processes MQTT payloads that modify properties of individual listbox options
    # (e.g., active status, labels, or selection state). It updates the internal options map
    # and triggers a rebuild of the listbox display.
    # Inputs:
    #     topic (str): The MQTT topic the message was received on.
    #     payload: The MQTT message payload containing the option update.
    #     widget_path (str): The full path of the listbox widget.
    #     base_mqtt_topic (str): The base MQTT topic for the application.
    # Outputs:
    #     None.
    def _on_option_mqtt_update_instance(
        self, topic, payload, widget_path, base_mqtt_topic
    ):
        import orjson  # Imported here to avoid circular dependency or top-level import issues

        try:
            payload_data = orjson.loads(payload)
            value = payload_data.get("val")  # 'val' contains the actual data

            # Extract option key from topic: e.g., OPEN-AIR/Connection/YAK/Frequency/widget_id/options/KEY/active
            parts = topic.split(TOPIC_DELIMITER)

            # Construct the expected prefix for this listbox
            expected_prefix_parts = [
                self.state_mirror_engine.base_topic,
                base_mqtt_topic,
                widget_path,
                "options",
            ]
            expected_prefix = TOPIC_DELIMITER.join(
                p for p in expected_prefix_parts if p
            )

            # Check if the topic starts with the expected prefix
            if not topic.startswith(expected_prefix):
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"⚠️ Topic '{topic}' does not match expected listbox option prefix '{expected_prefix}'. Ignoring update.",
                        **_get_log_args(),
                    )
                return

            # Remove the prefix to get the relative parts: KEY/property_name
            remaining_parts_str = topic[len(expected_prefix) :].strip(TOPIC_DELIMITER)
            remaining_parts = remaining_parts_str.split(TOPIC_DELIMITER)

            if len(remaining_parts) < 2:
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"⚠️ Insufficient parts in listbox option topic '{topic}'. Expected KEY/property_name. Remaining: {remaining_parts_str}",
                        **_get_log_args(),
                    )
                return

            option_key = remaining_parts[0]
            property_name = remaining_parts[1]

            if option_key not in self.options_map:
                self.options_map[option_key] = {}

            if property_name == "active":
                # Convert MQTT val (boolean True/False) to string 'true'/'false' for storage
                self.options_map[option_key]["active"] = str(value).lower()
            elif property_name == "label_active":
                self.options_map[option_key]["label_active"] = value
            elif property_name == "label_inactive":
                self.options_map[option_key]["label_inactive"] = value
            elif property_name == "selected":
                # This handles the case where the MQTT message explicitly sets selection
                # The payload val is boolean, convert to 'true'/'false' for internal config consistency
                self.options_map[option_key]["selected"] = str(value).lower()
                if value is True:
                    # If this option is selected, ensure the StringVar reflects its label
                    current_label = self.options_map[option_key].get("label_active")
                    if (
                        current_label
                        and self.selected_option_var.get() != current_label
                    ):
                        self.selected_option_var.set(
                            current_label
                        )  # Update selected var

            self._rebuild_listbox_display_instance()  # Redraw the listbox

        except (orjson.JSONDecodeError, AttributeError) as e:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌ Error processing listbox MQTT update for {topic}: {e}. Payload: {payload}",
                    **_get_log_args(),
                )