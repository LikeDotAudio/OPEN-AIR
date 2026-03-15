# listbox/dynamic_guimake_listbox.py
#
# This file provides the BuilderListboxCreator class for dynamically creating Listbox widgets in the GUI.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20250821.200641.1

import tkinter as tk
from tkinter import ttk
import os
import inspect
from decimal import Decimal, InvalidOperation
import time
import orjson

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

from workers.Command_Router.mqtt.mqtt_subscriber_router import (
    MqttSubscriberRouter,
)  # Import MqttSubscriberRouter
from workers.Command_Router.mqtt.mqtt_topic_utils import (
    get_topic,
    TOPIC_DELIMITER,
)  # Import get_topic and TOPIC_DELIMITER

from workers.styling.style import THEMES, DEFAULT_THEME
from managers.Display.transparency.transparency_mixin import TransparencyMixin
from workers.handlers.widget_event_binder import bind_variable_trace

# --- Global Scope Variables ---
current_file = f"{os.path.basename(__file__)}"

# --- Constants ---
DEFAULT_PAD_X = 5
DEFAULT_PAD_Y = 2


class BuilderListboxCreator(TransparencyMixin):
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
    #     tk.Frame: The created frame containing the listbox widget, or None on failure.
    def make_listbox(
        self, parent_widget, config_data, context=None, **kwargs
    ):  # Updated signature
        """Creates a listbox menu for multiple choice options."""
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️📑 [BUILDER] Entering make_listbox")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config_data}")

        current_function_name = inspect.currentframe().f_code.co_name

        # Extract widget-specific config from config_data
        label = config_data.get("label_active") or config_data.get("label", "")
        config = config_data  # config_data is the config
        path = config_data.get("path")  # Path for this widget

        # ⚡ HARDENED INTERFACE: Extract from context if available
        if BUILDER_DEBUG: builder_logger.trace("🔗🗂️⚙️ [CONTEXT] Extracting engine and router context...")
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            builder_instance = context.builder_instance
            if BUILDER_DEBUG: builder_logger.debug("✅🆗💻 [CONTEXT] Successfully extracted from WidgetContext object.")
        else:
            state_mirror_engine = self.state_mirror_engine
            subscriber_router = self.subscriber_router
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance") or self
            if BUILDER_DEBUG: builder_logger.debug("⚠️🔔🖱️ [CONTEXT] Context missing; fell back to self/kwargs.")

        if BUILDER_DEBUG: builder_logger.debug(f"🔬⚡️📑 [BUILDER] Materializing listbox for '{label}' at path '{path}'.")

        try:
            # Use Canvas for sub_frame to support alpha background slicing
            if BUILDER_DEBUG: builder_logger.trace(f"🏗️🪟🎨 [CONSTRUCT] Creating canvas frame for listbox '{label}'")
            sub_frame = tk.Canvas(
                parent_widget, 
                bd=0,
                highlightthickness=0,
                relief="flat",
                width=200, 
                height=150
            )
            sub_frame.pack_propagate(False)

            sub_frame.grid_rowconfigure(1, weight=1)
            sub_frame.grid_columnconfigure(0, weight=1)
            
            # Apply Industrial Transparency
            if hasattr(self, '_apply_transparency'):
                if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to listbox canvas.")
                self._apply_transparency(sub_frame, sub_frame, config, builder_instance)

            def redraw_listbox_label(*args):
                if not sub_frame.winfo_exists(): return
                w = sub_frame.winfo_width()
                if w <= 1: return
                if BUILDER_DEBUG: builder_logger.trace(f"🔄🎨🔤 [REDRAW] Redrawing listbox label for '{label}'")
                sub_frame.delete("industrial_text")
                
                if label:
                    sub_frame.create_text(
                        DEFAULT_PAD_X, 12, text=label, anchor="w",
                        fill="white", font=("TkDefaultFont", 10, "bold"),
                        tags="industrial_text"
                    )

            listbox_frame = tk.Frame(sub_frame, bd=0, highlightthickness=0)
            # Add top padding if there is a label to avoid overlap
            pady_top = 25 if label else 2
            listbox_frame.grid(row=1, column=0, sticky="nsew", pady=(pady_top, 2))
            sub_frame.lb_frame = listbox_frame

            listbox_frame.grid_rowconfigure(0, weight=1)
            listbox_frame.grid_columnconfigure(0, weight=1)

            if BUILDER_DEBUG: builder_logger.trace(f"🏗️🔳🕹️ [CONSTRUCT] Instantiating tk.Listbox.")
            scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL)
            
            # --- STYLING: MATCH DARK THEME ---
            colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
            lb_fg = colors.get("treeview_fg", "#dcdcdc")
            lb_select_bg = colors.get("treeview_selected_bg", "#007acc")
            lb_select_fg = colors.get("treeview_selected_fg", "#ffffff")

            listbox = tk.Listbox(
                listbox_frame,
                yscrollcommand=scrollbar.set,
                exportselection=False,
                selectmode=tk.SINGLE,
                height=5,
                width=30,
                fg=lb_fg,
                selectbackground=lb_select_bg,
                selectforeground=lb_select_fg,
                borderwidth=0,
                highlightthickness=1,
                highlightbackground=colors.get("border", "#555555")
            )

            scrollbar.config(command=listbox.yview)
            scrollbar.grid(row=0, column=1, sticky="ns")
            listbox.grid(row=0, column=0, sticky="nsew")
            
            def sync_bg():
                if BUILDER_DEBUG: builder_logger.trace(f"🔄👻🎨 [SYNC] Syncing listbox components background.")
                bg = sub_frame.cget("bg")
                listbox_frame.config(bg=bg)
                listbox.config(bg=bg)
                redraw_listbox_label()
            
            sub_frame._draw = sync_bg
            sub_frame.bind("<Configure>", lambda e: redraw_listbox_label(), add="+")

            self.options_map = config.get("options", {})  # Stored as instance variable
            # Ensure it is a dict
            if isinstance(self.options_map, list):
                if BUILDER_DEBUG: builder_logger.debug(f"⚠️🔔🔡 [CONFIG] Options for listbox '{label}' is a list, converting to dict.")
                self.options_map = {str(i): v for i, v in enumerate(self.options_map)}

            self.listbox = listbox  # Stored as instance variable
            self.selected_option_var = tk.StringVar(sub_frame)

            # Store widget instance for debugging/reference
            self._listbox_widget_instance = listbox

            # --- MQTT Subscription for dynamic updates ---
            if subscriber_router and state_mirror_engine:
                wildcard_option_topic = state_mirror_engine.calculate_topic(f"{path}/options/#", base_mqtt_topic_from_path)
                if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔄 [MQTT] Subscribing to wildcard options topic: {wildcard_option_topic}")
                # Pass necessary context to the instance method
                subscriber_router.subscribe_to_topic(
                    topic_filter=wildcard_option_topic,
                    callback_func=lambda msg, wp=path, bmt=base_mqtt_topic_from_path: self._on_option_mqtt_update_instance(
                        msg.topic, msg.payload, wp, bmt
                    ),  # Use instance method as callback
                )

            # Initial display build
            self._rebuild_listbox_display_instance(label)

            def update_listbox_from_var(*args):
                """Sync Listbox selection when StringVar changes (e.g. from MQTT)"""
                new_selection_val = self.selected_option_var.get()
                if BUILDER_DEBUG: builder_logger.trace(f"🔄✨🔢 [SYNC] StringVar change detected for listbox '{label}': {new_selection_val}")
                if not new_selection_val:
                    self.listbox.select_clear(0, tk.END)
                    return

                # Find the label for this value to highlight in listbox
                target_label = None
                for key, opt in self.options_map.items():
                    val = str(opt.get("value", key))
                    if val == str(new_selection_val):
                        target_label = opt.get("label_active", key)
                        opt["selected"] = "true"
                    else:
                        opt["selected"] = "false"

                if target_label and target_label in self.listbox.get(0, tk.END):
                    idx = self.listbox.get(0, tk.END).index(target_label)
                    self.listbox.select_clear(0, tk.END)
                    self.listbox.select_set(idx)
                    self.listbox.see(idx)

            self.selected_option_var.trace_add("write", update_listbox_from_var)

            def on_select(event):
                widget = event.widget
                selection_indices = widget.curselection()
                if not selection_indices:
                    return

                selected_index = selection_indices[0]
                selected_label = widget.get(selected_index)
                if BUILDER_DEBUG: builder_logger.info(f"🖱️👆📑 [INPUT] User selected item index {selected_index} ('{selected_label}') in listbox '{label}'")

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
                        selected_value = self.options_map[selected_key].get("value", selected_key)
                        
                        # 1. Update selection status for all options via MQTT
                        for key, opt in self.options_map.items():
                            is_selected = key == selected_key
                            topic_path = state_mirror_engine.calculate_topic(f"{path}/options/{key}/selected", base_mqtt_topic_from_path)
                            payload = orjson.dumps({"val": is_selected, "ts": time.time()})
                            if BUILDER_DEBUG: builder_logger.trace(f"📡🔴📡 [MQTT] Updating option '{key}' selection state to: {is_selected}")
                            state_mirror_engine.publish_command(topic_path, payload)

                        # 2. Update main value variable - now stores the VALUE, not label
                        self.selected_option_var.set(selected_value)

                        if BUILDER_DEBUG: builder_logger.debug(f"⚡🔴📡 [EVENT] Listbox '{label}' selection update. Broadcasting main value '{selected_value}'.")
                except Exception as e:
                    if BUILDER_DEBUG:
                        builder_logger.exception(f"❌🚫🛑 [ERROR] failure in listbox selection for '{label}'")

            listbox.bind("<<ListboxSelect>>", on_select)

            if path:
                if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [MQTT] Registering listbox at path '{path}'")
                widget_id = path
                # Register the StringVar with the StateMirrorEngine for MQTT updates
                topic = state_mirror_engine.register_widget(
                    widget_id,
                    self.selected_option_var,
                    base_mqtt_topic_from_path,
                    config,
                )

                # Subscribe to this widget's topic to receive updates for its selected value
                if subscriber_router and topic:
                    if BUILDER_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing to topic: {topic}")
                    subscriber_router.subscribe_to_topic(
                        topic, state_mirror_engine.sync_incoming_mqtt_to_gui
                    )

                # Trace for broadcasting the overall selected option
                def on_gui_change(*args):
                    if BUILDER_DEBUG: builder_logger.debug(f"⚡🔴📡 [EVENT] Overall listbox '{label}' value change. Broadcasting.")
                    state_mirror_engine.broadcast_gui_change_to_mqtt(path)
                
                self.selected_option_var.trace_add("write", on_gui_change)

                # Initialize state
                if BUILDER_DEBUG: builder_logger.trace(f"🔄⏳🔋 [STATE] Initializing state from cache/broker for '{path}'")
                state_mirror_engine.initialize_widget_state(path)

            if BUILDER_DEBUG: builder_logger.success(f"✅🆗📑 [SUCCESS] The listbox '{label}' has materialized!")
            return sub_frame

        except Exception as e:
            if BUILDER_DEBUG:
                builder_logger.exception(f"❌🚫🛑 [ERROR] Critical failure creating listbox '{label}'")
            return None

    # Rebuilds the visual display of the listbox based on the current options map.
    def _rebuild_listbox_display_instance(self, label="Listbox"):
        lb = self.listbox
        current_selection_val = self.selected_option_var.get()

        lb.delete(0, tk.END)
        
        # Filter for active options (default to active if not specified)
        active_options = {
            k: v
            for k, v in self.options_map.items()
            if str(v.get("active", "true")).lower() in ["true", "yes"]
        }

        # Sort by value
        sorted_options = sorted(active_options.items(), key=lambda x: str(x[1].get("value", x[0])))

        for key, opt in sorted_options:
            display_label = opt.get("label_active", key)
            lb.insert(tk.END, display_label)
            
            # Check if this item should be selected
            opt_val = str(opt.get("value", key))
            if opt_val == str(current_selection_val):
                idx = lb.get(0, tk.END).index(display_label)
                lb.select_set(idx)
                lb.see(idx)

    # Callback function for updating listbox options via incoming MQTT messages.
    def _on_option_mqtt_update_instance(self, topic, payload, widget_path, base_mqtt_topic):
        try:
            payload_data = orjson.loads(payload)
            value = payload_data.get("val")

            # Construct expected prefix
            expected_prefix = self.state_mirror_engine.calculate_topic(f"{widget_path}/options", base_mqtt_topic)

            if not topic.startswith(expected_prefix):
                return

            # Extract KEY/property
            rel_path = topic[len(expected_prefix):].strip(TOPIC_DELIMITER)
            parts = rel_path.split(TOPIC_DELIMITER)

            if len(parts) < 2: return

            option_key = parts[0]
            property_name = parts[1]

            # MECHANISM TO ADD: If key doesn't exist, create it!
            if option_key not in self.options_map:
                self.options_map[option_key] = {"active": "true"}
                if LOCAL_DEBUG: logger.debug(f"➕ MQTT added new option '{option_key}' to listbox.")

            if property_name == "active":
                self.options_map[option_key]["active"] = str(value).lower()
            elif property_name == "label_active":
                self.options_map[option_key]["label_active"] = value
            elif property_name == "value":
                self.options_map[option_key]["value"] = value
            elif property_name == "selected":
                self.options_map[option_key]["selected"] = str(value).lower()
                if value is True:
                    new_val = self.options_map[option_key].get("value", option_key)
                    if self.selected_option_var.get() != str(new_val):
                        self.selected_option_var.set(new_val)

            # Redraw
            self._rebuild_listbox_display_instance()

        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception("❌ Error in listbox MQTT update")
