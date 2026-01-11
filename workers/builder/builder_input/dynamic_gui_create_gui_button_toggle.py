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
# Version 20260110.2115.6

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
    ):  
        current_function_name = inspect.currentframe().f_code.co_name
        
        # Extract label early for logging
        label = config_data.get("label_active", "Unknown_Label")
        
        # 1. Debug Entry
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🧪 Great Scott! Entering '{current_function_name}' for label: {label}",
                **_get_log_args(),
            )

        # Extract only widget-specific config from config_data
        config = config_data  # config_data is the config
        path = config_data.get("path")  # Path for this widget

        # Access global context directly from self
        state_mirror_engine = self.state_mirror_engine
        subscriber_router = self.subscriber_router
        base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔬⚡️ Engineering toggle button mechanism for '{label}'...",
                **_get_log_args(),
            )

        try:
            # Create the container frame
            sub_frame = ttk.Frame(parent_widget)

            # Parse Options
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
            button_font_size_from_layout = layout.get("font", 10) # Default to 10 if missing
            button_sticky = layout.get("sticky", "nsew") 

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🧐 Layout Analysis: H={button_height_from_layout}, W={button_width_from_layout}, Font={button_font_size_from_layout}",
                    **_get_log_args(),
                )

            # --- Frame Sizing Logic ---
            if button_width_from_layout is not None or button_height_from_layout is not None:
                sub_frame.pack_propagate(False) # Stop sub_frame from resizing to content

                if button_height_from_layout is not None:
                    sub_frame.config(height=button_height_from_layout)

                if button_width_from_layout is not None:
                    sub_frame.config(width=button_width_from_layout)
                elif button_height_from_layout is not None: 
                    # Height is present, but width is not. Calculate width.
                    current_button_text = on_text if is_on else off_text
                    try:
                        style = ttk.Style()
                        font_name = style.lookup('TButton', 'font')
                        if font_name:
                            button_font = tkFont.Font(font=font_name)
                            text_pixel_width = button_font.measure(current_button_text)
                            desired_sub_frame_width = text_pixel_width + 40 
                            sub_frame.config(width=desired_sub_frame_width)
                        else:
                            sub_frame.config(width=100) # Fallback
                    except Exception as e:
                        sub_frame.config(width=100) # Fallback

            # --- Style & Font Configuration ---
            if path:
                safe_path = path.replace("/", "_").replace(".", "_").replace(" ", "_").replace(":", "_")
            else:
                safe_path = f"gen_{id(sub_frame)}"
                
            unique_style_name = f"{safe_path}.Custom.TButton"
            unique_selected_style_name = f"{safe_path}.Selected.Custom.TButton"

            font_family = "TkDefaultFont"
            font_slant = "roman"
            font_weight_normal = "normal"

            try:
                style = ttk.Style()
                # Lookup base font properties
                font_config = style.lookup('TButton', 'font')
                if font_config:
                    temp_font = tkFont.Font(font=font_config)
                    font_family = temp_font.actual("family")
                    font_slant = temp_font.actual("slant")
                    font_weight_normal = temp_font.actual("weight") if "weight" in temp_font.actual() else "normal"
            except Exception as e:
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"⚠️ Warning: Could not lookup base TButton font: {e}. Using defaults.",
                        **_get_log_args(),
                    )

            # Define fonts
            inactive_font_tuple = (font_family, button_font_size_from_layout, font_weight_normal, font_slant)
            active_font_tuple = (font_family, button_font_size_from_layout, "bold", font_slant)

            # Configure Styles
            
            # 1. Normal (Inactive) Style
            # Inactive = Default BG, Hover = Light Grey
            if not style.layout(unique_style_name):
                 style.layout(unique_style_name, style.layout("TButton"))
                 
            style.configure(unique_style_name, font=inactive_font_tuple)
            style.map(unique_style_name, 
                font=[('active', active_font_tuple), ('!active', inactive_font_tuple)],
                background=[('active', 'light grey')]  # <--- Light Grey when hovered
            )

            # 2. Selected (Active) Style
            # Active = Orange, Hover = Blue
            if not style.layout(unique_selected_style_name):
                 style.layout(unique_selected_style_name, style.layout("TButton"))

            # Base configuration for Selected State
            style.configure(unique_selected_style_name, 
                font=active_font_tuple,
                background="orange",
                foreground="black"
            )
            
            # Map for hover/active states
            style.map(unique_selected_style_name,
                background=[('active', 'blue'), ('!active', 'orange')],  # <--- Blue on hover, Orange otherwise
                foreground=[('active', 'white'), ('!active', 'black')]   # <--- White text on Blue for contrast
            )
            
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🎨 Styled '{unique_selected_style_name}': Orange (Active) -> Blue (Hover).",
                    **_get_log_args(),
                )

            # --- Create Button ---
            # Initial style based on state
            initial_style = unique_selected_style_name if is_on else unique_style_name
            
            button = ttk.Button(
                sub_frame, 
                text=on_text if is_on else off_text, 
                style=initial_style
            )
            
            # Packing the button
            button.pack(expand=True, fill='both')

            # Debug dimensions
            if app_constants.global_settings["debug_enabled"]:
                try:
                    parent_widget.winfo_toplevel().update_idletasks() 
                    debug_logger(
                        message=f"📏 Sub_frame dimensions: W={sub_frame.winfo_width()}, H={sub_frame.winfo_height()}",
                        **_get_log_args(),
                    )
                except Exception:
                    pass 

            # --- Internal Handlers ---

            def update_button_state(*args):
                # Updates the button's appearance based on its current state.
                current_state = state_var.get()
                if current_state:  
                    # Button is ON (Orange/Blue)
                    button.config(text=on_text, style=unique_selected_style_name)
                else:  
                    # Button is OFF (Default/Light Grey)
                    button.config(text=off_text, style=unique_style_name)

            def on_button_click(event):
                # Shift key is bit 1 of the state mask (0x0001)
                is_shift_pressed = (event.state & 0x0001) != 0

                if is_shift_pressed:
                    # Latching behavior
                    if not state_var.get():
                        state_var.set(True)
                else:
                    # Normal toggle behavior
                    state_var.set(not state_var.get())

            # --- Binding & Wiring ---
            button.bind("<Button-1>", on_button_click)
            
            # Ensure visual state matches var immediately
            update_button_state() 

            if path:
                self.topic_widgets[path] = (state_var, update_button_state)

                # --- MQTT Wiring ---
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

                # 3. Also trace changes to update the button state (Local GUI update)
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
                    message=f"✅ SUCCESS! The toggle button '{label}' is active, hovering, and spectral!",
                    **_get_log_args(),
                )
                
            return sub_frame

        except Exception as e:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌💥 KABOOM! The toggle button for '{label}' went into a paradoxical state! Error: {e}",
                    **_get_log_args(),
                )
            return None