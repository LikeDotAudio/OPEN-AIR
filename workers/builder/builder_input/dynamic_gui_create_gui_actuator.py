# builder_input/dynamic_gui_create_gui_actuator.py
#
# This file provides the GuiActuatorCreatorMixin class for creating simple actuator buttons in the GUI.
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
# Version 20260110.2145.3



import os
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import inspect
import orjson
import time

current_file=os.path.basename(__file__)
version=current_version = "20260110.2135.2"
# --- Module Imports ---
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config
from workers.mqtt.mqtt_publisher_service import publish_payload

app_constants = Config.get_instance()  # Get the singleton instance
from workers.mqtt.mqtt_topic_utils import get_topic

# --- Constants ---
DEFAULT_PAD_X = 5
DEFAULT_PAD_Y = 2
TOPIC_DELIMITER = "/"


class GuiActuatorCreatorMixin:
    """
    A mixin class that provides the functionality for creating a simple
    actuator button widget that triggers an action.
    """

    # Creates a button that acts as a simple actuator, triggering actions via MQTT.
    # This method sets up a button that, when pressed and released, publishes MQTT
    # commands to a specified topic. It also publishes the button's configuration
    # and subscribes to status updates.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): Configuration for the actuator button.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     ttk.Frame: The created frame containing the actuator button, or None on failure.
    def _create_gui_actuator(
        self, parent_widget, config_data, **kwargs
    ):  
        """Creates a button that acts as a simple actuator."""
        current_function_name = inspect.currentframe().f_code.co_name

        # Extract labels for both states
        label = config_data.get("label", "Actuator")
        text_active = config_data.get("label_active", label)
        text_inactive = config_data.get("label_inactive", label)
        
        config = config_data  # config_data is the config
        path = config_data.get("path")

        # Access global context directly from self
        state_mirror_engine = self.state_mirror_engine
        subscriber_router = self.subscriber_router
        base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔬⚡️ Entering '{current_function_name}' to construct an actuator for '{label}'.",
                **_get_log_args(),
            )

        try:
            # Create a frame to hold the label and button
            sub_frame = ttk.Frame(parent_widget)  # Use parent_widget here
            sub_frame.grid_rowconfigure(0, weight=1)
            sub_frame.grid_columnconfigure(0, weight=1)

            layout = config.get("layout", {})
            button_height_from_layout = layout.get("height")
            button_width_from_layout = layout.get("width")
            button_font_size_from_layout = layout.get("font", 10) 

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"DEBUG: Layout height: {button_height_from_layout}, width: {button_width_from_layout}, font: {button_font_size_from_layout}",
                    **_get_log_args(),
                )

            # Control sub_frame dimensions based on layout
            if button_width_from_layout is not None or button_height_from_layout is not None:
                sub_frame.grid_propagate(False) # Stop sub_frame from resizing to content

                if button_height_from_layout is not None:
                    sub_frame.config(height=button_height_from_layout)
                    
                if button_width_from_layout is not None:
                    sub_frame.config(width=button_width_from_layout)
                elif button_height_from_layout is not None: # Height is present, but width is not
                    # Calculate width based on text + 40px margin
                    try:
                        style = ttk.Style()
                        font_name = style.lookup('TButton', 'font')
                        if font_name:
                            button_font = tkFont.Font(font=font_name)
                            # Measure the wider of the two strings to ensure fit
                            width_active = button_font.measure(text_active)
                            width_inactive = button_font.measure(text_inactive)
                            text_pixel_width = max(width_active, width_inactive)
                            
                            desired_sub_frame_width = text_pixel_width + 40 
                            sub_frame.config(width=desired_sub_frame_width)
                        else:
                            sub_frame.config(width=100) 
                    except Exception as e:
                        sub_frame.config(width=100) 

            # --- STYLE & FONT CONFIGURATION ---
            if path:
                safe_path = path.replace("/", "_").replace(".", "_").replace(" ", "_").replace(":", "_")
            else:
                safe_path = f"gen_{id(sub_frame)}"

            # Naming convention: {Unique}.Custom.TButton
            unique_style_name = f"{safe_path}.Custom.TButton"
            unique_selected_style_name = f"{safe_path}.Custom.Selected.TButton"
            
            # Resolve Font
            font_family = "TkDefaultFont"
            font_slant = "roman"
            font_weight = "normal"
            try:
                style = ttk.Style()
                font_config = style.lookup('TButton', 'font')
                if font_config:
                    temp_font = tkFont.Font(font=font_config)
                    font_family = temp_font.actual("family")
            except Exception:
                pass

            font_tuple = (font_family, button_font_size_from_layout, font_weight, font_slant)
            font_tuple_bold = (font_family, button_font_size_from_layout, "bold", font_slant)

            # Configure Normal Style
            if not style.layout(unique_style_name):
                 style.layout(unique_style_name, style.layout("TButton"))
            style.configure(unique_style_name, font=font_tuple)
            
            # Configure Selected (Active) Style - Orange Background & BOLD Font
            if not style.layout(unique_selected_style_name):
                 style.layout(unique_selected_style_name, style.layout("TButton"))
            
            style.configure(unique_selected_style_name, 
                font=font_tuple_bold,
                background="orange",
                foreground="black"
            )
            # Map for hover states on selected
            style.map(unique_selected_style_name,
                background=[('active', 'dark orange'), ('!active', 'orange')],
                foreground=[('active', 'black'), ('!active', 'black')]
            )

            # Initialize with Inactive text and style
            button = ttk.Button(sub_frame, text=text_inactive, style=unique_style_name)

            # STORE LABELS & STYLES ON BUTTON OBJECT FOR RETRIEVAL LATER
            button._text_active = text_active
            button._text_inactive = text_inactive
            button._style_active = unique_selected_style_name
            button._style_inactive = unique_style_name

            # FIX: Use sticky="nsew" to force button to fill the fixed-size sub_frame
            button.grid(
                row=0,
                column=0,
                sticky="nsew", 
                padx=DEFAULT_PAD_X,
                pady=DEFAULT_PAD_Y,
            )

            def on_press(event):
                # 1. IMMEDIATE LOCAL FEEDBACK (The Snap!)
                button.config(text=button._text_active, style=button._style_active)
                
                # 2. Network Action
                action_path = f"{path}/trigger"
                topic = get_topic(self.state_mirror_engine.base_topic, base_mqtt_topic_from_path, action_path)
                payload = orjson.dumps({"val": True, "ts": time.time()})

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"▶️ GUI ACTION: Activating actuator '{label}'",
                        file=current_file,
                        version=current_version,
                        function=f"{self.__class__.__name__}.{current_function_name}",
                    )
                self.state_mirror_engine.publish_command(topic, payload)

            def on_release(event):
                # 1. IMMEDIATE LOCAL FEEDBACK (The Release!)
                button.config(text=button._text_inactive, style=button._style_inactive)

                # 2. Network Action
                action_path = f"{path}/trigger"
                topic = get_topic(self.state_mirror_engine.base_topic, base_mqtt_topic_from_path, action_path)
                payload = orjson.dumps({"val": False, "ts": time.time()})

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"⏹️ GUI ACTION: Deactivating actuator '{label}'",
                        file=current_file,
                        version=current_version,
                        function=f"{self.__class__.__name__}.{current_function_name}",
                    )
                self.state_mirror_engine.publish_command(topic, payload)

            button.bind("<ButtonPress-1>", on_press)
            button.bind("<ButtonRelease-1>", on_release)

            if path:
                self.topic_widgets[path] = button

                # --- New MQTT Wiring ---
                widget_id = path

                # Publish the static configuration
                config_topic = get_topic(
                    self.state_mirror_engine.base_topic, base_mqtt_topic_from_path, widget_id, "config"
                )
                config_payload = orjson.dumps(config)
                publish_payload(config_topic, config_payload, retain=True)

                # Subscribe to status (Back up in case of remote actuation)
                status_topic = f"{get_topic('OPEN-AIR', base_mqtt_topic_from_path, widget_id)}/active"
                self.subscriber_router.subscribe_to_topic(
                    status_topic, self._on_actuator_state_update
                )

            return sub_frame

        except Exception as e:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌ The actuator '{label}' has short-circuited! Error: {e}",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                )
            return None

    # Callback function to update the visual state of the actuator button based on MQTT messages.
    # This method parses an incoming MQTT payload, extracts the active state (True/False),
    # and updates the button's style accordingly to indicate its active or inactive status.
    def _on_actuator_state_update(self, topic, payload):
        import orjson

        try:
            payload_data = orjson.loads(payload)
            is_active = payload_data.get("val")

            # Derive widget_id from topic
            topic_without_active = topic.rsplit(TOPIC_DELIMITER, 1)[0]
            expected_prefix = f"OPEN-AIR{TOPIC_DELIMITER}{self.state_mirror_engine.base_topic}{TOPIC_DELIMITER}"
            
            if topic_without_active.startswith(expected_prefix):
                key_in_topic_widgets = topic_without_active.replace(expected_prefix, "", 1)
            else:
                key_in_topic_widgets = topic_without_active 

            button = self.topic_widgets.get(key_in_topic_widgets)
            
            if button:
                # Use stored styles to avoid reconstruction errors
                if is_active:
                    button.config(style=button._style_active, text=button._text_active)
                else:
                    button.config(style=button._style_inactive, text=button._text_inactive)

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"ℹ️ GUI ACTUATOR: Actuator '{key_in_topic_widgets}' updated via MQTT. Active: {is_active}",
                        **_get_log_args(),
                    )
            else:
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"⚠️ GUI ACTUATOR: Button widget not found for key: {key_in_topic_widgets}",
                        **_get_log_args(),
                    )

        except (orjson.JSONDecodeError, AttributeError) as e:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌ Error processing actuator MQTT update for {topic}: {e}. Payload: {payload}"
                )