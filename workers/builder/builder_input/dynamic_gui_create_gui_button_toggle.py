# builder_input/dynamic_gui_create_gui_button_toggle.py
#
# This file provides the GuiButtonToggleCreatorMixin class for creating toggle button widgets in the GUI.
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

import os
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
import inspect
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance
from workers.handlers.widget_event_binder import bind_variable_trace
from workers.mqtt.mqtt_topic_utils import get_topic


# --- Global Scope Variables ---
current_file = f"{os.path.basename(__file__)}"

TOPIC_DELIMITER = "/"


class GuiButtonToggleCreatorMixin:
    # Creates a single button that toggles between two states (e.g., ON/OFF).
    # This method sets up a button with dynamic text and styling based on its boolean state.
    # It supports both normal toggling behavior and a "latching" mode when the Shift key is pressed,
    # and integrates with the state management engine for MQTT synchronization.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): Configuration for the toggle button.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     ttk.Frame: The created frame containing the toggle button, or None on failure.
    def _create_gui_button_toggle(
        self, parent_widget, config_data, **kwargs
    ):  # Updated signature
        print(f"--- DEBUG: _create_gui_button_toggle entered for label: {config_data.get('label_active')} ---")
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"DEBUG (Toggle Button - Entry): app_constants.global_settings['debug_enabled'] is {app_constants.global_settings['debug_enabled']}",
                **_get_log_args(),
            )
        """Creates a single button that toggles between two states (e.g., ON/OFF)."""
        current_function_name = inspect.currentframe().f_code.co_name

        # Extract only widget-specific config from config_data
        label = config_data.get("label_active")
        config = config_data  # config_data is the config
        path = config_data.get("path")  # Path for this widget

        # Access global context directly from self
        state_mirror_engine = self.state_mirror_engine
        subscriber_router = self.subscriber_router
        base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔬⚡️ Entering '{current_function_name}' to engineer a toggle button for '{label}'.",
                **_get_log_args(),
            )

        try:
            sub_frame = ttk.Frame(parent_widget)  # Use parent_widget here

            options_map = config.get("options", {})
            on_config = options_map.get("ON", {})
            off_config = options_map.get("OFF", {})
            on_text = on_config.get("label_active", "ON")
            off_text = off_config.get("label_inactive", "OFF")

            is_on = options_map.get("ON", {}).get("selected", False)

            state_var = tk.BooleanVar(value=is_on)

            # Get layout parameters
            layout = config.get("layout", {})
            button_height_from_layout = layout.get("height")
            button_width_from_layout = layout.get("width")
            button_font_size_from_layout = layout.get("font") # New: Get font size from layout
            button_sticky = layout.get("sticky", "nsew") # Default to nsew for fill

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"DEBUG (Toggle Button): Layout height: {button_height_from_layout}, width: {button_width_from_layout}, font: {button_font_size_from_layout}",
                    **_get_log_args(),
                )

            # Configure sub_frame dimensions based on layout
            if button_width_from_layout is not None or button_height_from_layout is not None:
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"DEBUG (Toggle Button): Calling sub_frame.pack_propagate(False)",
                        **_get_log_args(),
                    )
                sub_frame.pack_propagate(False) # Stop sub_frame from resizing to content

                if button_height_from_layout is not None:
                    sub_frame.config(height=button_height_from_layout)
                    if app_constants.global_settings["debug_enabled"]:
                        debug_logger(
                            message=f"DEBUG (Toggle Button): Configured sub_frame height: {button_height_from_layout}",
                            **_get_log_args(),
                        )

                if button_width_from_layout is not None:
                    sub_frame.config(width=button_width_from_layout)
                    if app_constants.global_settings["debug_enabled"]:
                        debug_logger(
                            message=f"DEBUG (Toggle Button): Configured sub_frame width: {button_width_from_layout}",
                            **_get_log_args(),
                        )
                elif button_height_from_layout is not None: # Height is present, but width is not
                    # Calculate width based on text + 40px margin
                    current_button_text = on_text if is_on else off_text
                    try:
                        style = ttk.Style()
                        font_name = style.lookup('TButton', 'font')
                        if font_name:
                            # Create a Font object to measure text
                            button_font = tkFont.Font(font=font_name)
                            text_pixel_width = button_font.measure(current_button_text)
                            desired_sub_frame_width = text_pixel_width + 40 # text width + 20px on each side
                            sub_frame.config(width=desired_sub_frame_width)
                            if app_constants.global_settings["debug_enabled"]:
                                debug_logger(
                                    message=f"DEBUG (Toggle Button): Calculated desired width for text '{current_button_text}': {desired_sub_frame_width}",
                                    **_get_log_args(),
                                )
                        else:
                            sub_frame.config(width=100) # Fallback
                            if app_constants.global_settings["debug_enabled"]:
                                debug_logger(
                                    message=f"DEBUG (Toggle Button): Fallback width 100 (font_name not found)",
                                    **_get_log_args(),
                                )
                    except Exception as e:
                        sub_frame.config(width=100) # Fallback
                        if app_constants.global_settings["debug_enabled"]:
                            debug_logger(
                                message=f"DEBUG (Toggle Button): Fallback width 100 (exception during font measure: {e})",
                                **_get_log_args(),
                            )

    # Configure the style for the button, including font.
    # Define a generic font family and fallback if style.lookup fails or is not available.
    font_family = "TkDefaultFont"
    font_slant = "roman"
    font_weight_normal = "normal"

    try:
        style = ttk.Style()
        font_config = style.lookup('TButton', 'font')
        if font_config:
            temp_font = tkFont.Font(font=font_config)
            font_family = temp_font.actual("family")
            font_slant = temp_font.actual("slant")
            # Attempt to get default weight, fallback to "normal"
            font_weight_normal = temp_font.actual("weight") if "weight" in temp_font.actual() else "normal"
    except Exception as e:
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"WARNING (Toggle Button): Could not lookup base TButton font: {e}. Using default.",
                **_get_log_args(),
            )
        # Fallback to defaults if lookup fails

    # Define inactive font (normal weight)
    inactive_font_tuple = (font_family, button_font_size_from_layout, font_weight_normal, font_slant)

    # Define active font (bold weight)
    active_font_tuple = (font_family, button_font_size_from_layout, "bold", font_slant)

    # Configure the 'Custom.TButton' style for inactive state
    style.configure("Custom.TButton", font=inactive_font_tuple)
    if app_constants.global_settings["debug_enabled"]:
        debug_logger(
            message=f"DEBUG (Toggle Button): Configured 'Custom.TButton' inactive style font to: {inactive_font_tuple}",
            **_get_log_args(),
        )

    # Map the font for 'active' state to be bold
    style.map("Custom.TButton", font=[('active', active_font_tuple), ('!active', inactive_font_tuple)])
    if app_constants.global_settings["debug_enabled"]:
        debug_logger(
            message=f"DEBUG (Toggle Button): Mapped 'Custom.TButton' active style font to: {active_font_tuple}",
            **_get_log_args(),
        )

    # Create the ttk.Button. Explicitly set style to "Custom.TButton"
    button = ttk.Button(sub_frame, text=on_text if is_on else off_text, style="Custom.TButton")

    # Update the display of sub_frame's actual dimensions if debug is enabled
    if app_constants.global_settings["debug_enabled"]:
        app_root.update_idletasks()  # Process all pending events to ensure widgets are updated
        debug_logger(
            message=f"DEBUG (Toggle Button): Actual sub_frame dimensions after configuration: width={sub_frame.winfo_width()}, height={sub_frame.winfo_height()}",
            **_get_log_args(),
        )

            def update_button_state(*args):

                # Updates the button's appearance based on its current state.
                current_state = state_var.get()
                if (
                    current_state
                ):  # Correct logic: The button is ON, so use the 'Selected' style.
                    button.config(text=on_text, style="Custom.Selected.TButton")
                else:  # The button is OFF, so use the default 'TButton' style.
                    button.config(text=off_text, style="Custom.TButton")

            def on_button_click(event):
                # Shift key is bit 1 of the state mask
                is_shift_pressed = (event.state & 0x0001) != 0

                if is_shift_pressed:
                    # Latching behavior: if it's already on, do nothing. If it's off, turn it on and keep it on.
                    if not state_var.get():
                        state_var.set(True)
                else:
                    # Normal toggle behavior
                    state_var.set(not state_var.get())

            button.bind("<Button-1>", on_button_click)
            update_button_state()  # Set initial text and style

            if path:
                self.topic_widgets[path] = (state_var, update_button_state)

                # --- New MQTT Wiring ---
                widget_id = path

                # 1. Register widget
                state_mirror_engine.register_widget(
                    widget_id, state_var, base_mqtt_topic_from_path, config
                )

                # 2. Bind variable trace for outgoing messages
                callback = lambda: state_mirror_engine.broadcast_gui_change_to_mqtt(
                    widget_id
                )
                bind_variable_trace(state_var, callback)

                # 3. Also trace changes to update the button state
                state_var.trace_add("write", update_button_state)

                # 4. Subscribe to topic for incoming messages
                topic = state_mirror_engine.get_widget_topic(widget_id)
                if topic:
                    subscriber_router.subscribe_to_topic(
                        topic, state_mirror_engine.sync_incoming_mqtt_to_gui
                    )

                # 5. Initialize the widget's state from the cache or broadcast.
                state_mirror_engine.initialize_widget_state(widget_id)

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"✅ SUCCESS! The toggle button '{label}' is alive!",
                    **_get_log_args(),
                )
            return sub_frame

        except Exception as e:
            debug_logger(
                message=f"❌ Error in {current_function_name} for '{label}': {e}"
            )
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"💥 KABOOM! The toggle button for '{label}' went into a paradoxical state! Error: {e}",
                    **_get_log_args(),
                )
            return None