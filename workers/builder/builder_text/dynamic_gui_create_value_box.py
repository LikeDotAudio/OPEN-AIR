# builder_text/dynamic_gui_create_value_box.py
#
# This file provides the ValueBoxCreatorMixin class for creating editable text box widgets in the GUI.
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
# Version 20260110.2220.2

import os
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import inspect

# --- Module Imports ---
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance
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

    # Creates an editable text box widget for displaying and modifying a single value.
    # This method sets up a Label (optional), an Entry box, and a Units label (optional).
    # It supports layout customization (width, height, font) and full MQTT synchronization.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): Configuration for the value box.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     ttk.Frame: The created frame containing the value box, or None on failure.
    def _create_gui_value_box(
        self, parent_widget, config_data, **kwargs
    ):  
        current_function_name = inspect.currentframe().f_code.co_name

        # Extract config
        label = config_data.get("label_active") or config_data.get("label", "ValueBox")
        config = config_data
        path = config_data.get("path")
        units = config_data.get("units") or config_data.get("unit", "")

        # Access global context
        state_mirror_engine = self.state_mirror_engine
        subscriber_router = self.subscriber_router
        base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")

        # 1. Debug Entry
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🧪 Great Scott! Entering '{current_function_name}' for '{label}'...",
                **_get_log_args(),
            )

        try:
            # Create the container frame
            sub_frame = ttk.Frame(parent_widget)
            
            # Configure Grid: Label (0), Entry (1), Units (2)
            sub_frame.grid_columnconfigure(1, weight=1) # Entry expands
            sub_frame.grid_rowconfigure(0, weight=1)    # Height expands

            # --- Layout Analysis ---
            layout = config.get("layout", {})
            box_height = layout.get("height")
            box_width = layout.get("width")
            font_size = layout.get("font", 10) # Default font 10
            custom_colour = layout.get("colour", None)
            
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🧐 Layout Analysis for '{label}': H={box_height}, W={box_width}, Font={font_size}, Colour={custom_colour}",
                    **_get_log_args(),
                )

            # --- Frame Sizing Logic ---
            if box_width is not None or box_height is not None:
                sub_frame.grid_propagate(False) # Stop resizing to content
                
                if box_height is not None:
                    sub_frame.config(height=box_height)
                
                if box_width is not None:
                    sub_frame.config(width=box_width)
                elif box_height is not None:
                    # Calculate default width if only height is given
                    sub_frame.config(width=120) # Reasonable default for a value box

            # --- Widgets Construction ---

            # 1. Label (Left side)
            # Only create if label is not empty/None
            if label and label != "X": # 'X' might be a placeholder in your config
                lbl_widget = ttk.Label(sub_frame, text=f"{label}:", font=("TkDefaultFont", font_size))
                if custom_colour:
                    lbl_widget.configure(foreground=custom_colour)
                lbl_widget.grid(row=0, column=0, padx=(0, DEFAULT_PAD_X), sticky="w")

            # 2. Entry Variable
            initial_value = config.get("value", "0")
            entry_value = tk.StringVar(value=initial_value)

            # 3. Entry Widget (Center)
            # Prepare Font
            entry_font = ("TkDefaultFont", font_size)
            
            style_name = "Custom.TEntry"
            if custom_colour:
                style_name = f"Custom.{path.replace('/', '_')}.TEntry"
                style = ttk.Style()
                style.configure(style_name, foreground=custom_colour)

            entry_widget = ttk.Entry(
                sub_frame, 
                textvariable=entry_value,
                font=entry_font,
                justify="center", # Center the text looks better for values
                style=style_name
            )
            
            # STICKY NSEW ensures it fills the calculated frame height/width!
            entry_widget.grid(row=0, column=1, sticky="nsew", padx=DEFAULT_PAD_X)

            # 4. Units Label (Right side)
            if units:
                units_widget = ttk.Label(sub_frame, text=units, font=("TkDefaultFont", font_size))
                if custom_colour:
                    units_widget.configure(foreground=custom_colour)
                units_widget.grid(row=0, column=2, padx=(DEFAULT_PAD_X, 0), sticky="e")

            # --- Event Binding ---
            
            # Handle Enter Key (Return) -> Transmit
            def on_return(event):
                val = entry_value.get()
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"⚡ User pressed ENTER on '{label}'. Transmitting: {val}",
                        **_get_log_args(),
                    )
                # Broadcast changes
                state_mirror_engine.broadcast_gui_change_to_mqtt(path)

            entry_widget.bind("<Return>", on_return)
            
            # Handle Focus Out -> Transmit (Optional, but good UX)
            def on_focus_out(event):
                # Only transmit if modified? For now, we rely on the Variable Trace or explicit Enter.
                pass 
            entry_widget.bind("<FocusOut>", on_focus_out)

            # --- MQTT Wiring ---
            if path:
                widget_id = path
                
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"🔌 Wiring '{label}' to MQTT path: {widget_id}",
                        **_get_log_args(),
                    )

                # 1. Register
                state_mirror_engine.register_widget(
                    widget_id, entry_value, base_mqtt_topic_from_path, config
                )

                # 2. Bind Trace (Outgoing)
                # Note: We rely on the trace to sync the cache locally, but typically use Enter for "Set" commands.
                # However, to maintain consistency with other widgets in this project:
                callback = lambda: state_mirror_engine.broadcast_gui_change_to_mqtt(widget_id)
                bind_variable_trace(entry_value, callback)

                # 3. Subscribe (Incoming)
                topic = state_mirror_engine.get_widget_topic(widget_id)
                if topic:
                    subscriber_router.subscribe_to_topic(
                        topic, state_mirror_engine.sync_incoming_mqtt_to_gui
                    )
                    if app_constants.global_settings["debug_enabled"]:
                         debug_logger(message=f"📡 Subscribed to: {topic}", **_get_log_args())

                # 4. Initialize
                state_mirror_engine.initialize_widget_state(widget_id)

            if app_constants.global_settings["debug_enabled"]:
                # Use update_idletasks to get real dimensions for logging
                try:
                    sub_frame.update_idletasks()
                    debug_logger(
                        message=f"✅ SUCCESS! ValueBox '{label}' created. Dim: {sub_frame.winfo_width()}x{sub_frame.winfo_height()}",
                        **_get_log_args(),
                    )
                except:
                    pass

            return sub_frame

        except Exception as e:
            debug_logger(
                message=f"❌ Error in {current_function_name} for '{label}': {e}"
            )
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"💥 KABOOM! The value box for '{label}' has spectacularly failed! Error: {e}",
                    **_get_log_args(),
                )
            return None

    # --- TEMPORAL ALIAS FOR BACKWARD COMPATIBILITY ---
    # The Widget Factory is looking for the old name. We bridge the gap here!
    _create_value_box = _create_gui_value_box