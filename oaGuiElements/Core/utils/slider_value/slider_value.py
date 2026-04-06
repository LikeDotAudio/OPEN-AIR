# slider_value/slider_value.py
from oaGuiFramework.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: slider_value/gui_slider_value.py

import os
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
import tkinter as tk
from tkinter import ttk
import inspect

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

from oaOchestration.Methods.widget_event_binder import bind_variable_trace
from oaComMQTT.Methods.mqtt_topic_utils import get_topic
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin


# --- Global Scope Variables ---
current_file = f"{os.path.basename(__file__)}"

# --- Constants ---
DEFAULT_PAD_X = 5
DEFAULT_PAD_Y = 2


class BuilderSliderValueCreator(TransparencyMixin):
    """
    A mixin class that provides the functionality for creating a
    slider widget combined with a text entry box.
    """

    def __init__(self):
        self.topic_widgets = {}

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        creator = BuilderSliderValueCreator()
        return creator.make_slider_value(parent_widget, config_data, context, **kwargs)

    # Creates a composite widget consisting of a slider and a text entry box.
    # This method sets up a slider for adjusting a numerical value, along with a text entry
    # field for precise input. The two are synchronized and connected to the state management engine.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): The configuration for the slider widget.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     tk.Frame: The created frame containing the composite widget, or None on failure.
    def make_slider_value(self, parent_widget, config_data, context=None, **kwargs):
        # Creates a slider and an entry box for a numerical value.
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬 Entering make_slider_value with config: {config_data}", level="TRACE")
        current_function_name = inspect.currentframe().f_code.co_name

        # Extract only widget-specific config from config_data
        label = config_data.get(
            "label_active", ""
        )  # Assuming label comes from config_data
        path = config_data.get("path")  # Path needs to be passed in config_data

        # ⚡ HARDENED INTERFACE: Extract from context if available
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            builder_instance = context.builder_instance
        else:
            state_mirror_engine = self.state_mirror_engine
            subscriber_router = self.subscriber_router
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance") or self

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬⚡️ Entering '{current_function_name}' to assemble a slider for '{label}'.", level="DEBUG")

        try:
            sub_frame = tk.Frame(parent_widget, bd=0, highlightthickness=0, relief="flat")  # Use parent_widget here
            
            # Apply Industrial Transparency
            if hasattr(self, '_apply_transparency'):
                self._apply_transparency(sub_frame, None, config_data, builder_instance)

            layout_config = config_data.get("layout", {})
            font_size = layout_config.get("font", 12)
            custom_font = ("Helvetica", font_size)

            # --- Layout Refactor: Start ---
            # Line 1: Label, Textbox, Units
            top_info_frame = tk.Canvas(sub_frame, bd=0, highlightthickness=0, relief="flat", height=30)
            top_info_frame.pack(side=tk.TOP, fill=tk.X, expand=True)
            
            # Apply Industrial Transparency to internal frames
            if hasattr(self, '_apply_transparency'):
                self._apply_transparency(top_info_frame, top_info_frame, config_data, builder_instance)

            top_info_frame._last_redraw_size = (0, 0)

            def redraw_labels(*args):
                if not top_info_frame.winfo_exists(): return
                w = top_info_frame.winfo_width()
                h = top_info_frame.winfo_height()
                if (w, h) == top_info_frame._last_redraw_size:
                    return
                if w <= 1: return
                top_info_frame._last_redraw_size = (w, h)
                
                top_info_frame.delete("industrial_text")
                
                # Draw Main Label (Left)
                top_info_frame.create_text(
                    5, h/2, text=f"{label}:", anchor="w", 
                    fill="white", font=custom_font, tags="industrial_text"
                )
                
                # Draw Units (Right)
                units_txt = config_data.get("units", "")
                top_info_frame.create_text(
                    w-5, h/2, text=units_txt, anchor="e", 
                    fill="white", font=custom_font, tags="industrial_text"
                )

            top_info_frame.bind("<Configure>", redraw_labels, add="+")

            entry_value = tk.StringVar(value=config_data.get("value", "0"))
            entry = ttk.Entry(
                top_info_frame,
                width=7,
                style="Custom.TEntry",
                textvariable=entry_value,
                justify=tk.RIGHT,
                font=custom_font
            )
            # Pack entry with right padding to avoid overlapping the units text
            u_txt = config_data.get("units", "")
            u_pad = 60 if u_txt else 5
            entry.pack(side=tk.RIGHT, padx=(DEFAULT_PAD_X, u_pad))

            def sync_bg():
                redraw_labels()
            
            sub_frame._draw = sync_bg
            min_val = float(config_data.get("min", "0"))
            max_val = float(config_data.get("max", "100"))

            # 🟢️️️ New fix: Create a custom style for a thicker slider
            style = ttk.Style(sub_frame)
            style_name = f"Thicker.{font_size}.Horizontal.TScale"
            
            slider_width = layout_config.get("width", 200)
            slider_height = layout_config.get("height", 40)

            style.configure(style_name, sliderlength=font_size * 2)
            slider = ttk.Scale(
                sub_frame,
                from_=min_val,
                to=max_val,
                orient=tk.HORIZONTAL,
                style=style_name,
            )

            slider.pack(
                side=tk.TOP,
                fill=tk.X,
                expand=True,
                padx=DEFAULT_PAD_X,
                pady=(0, DEFAULT_PAD_Y),
            )

            try:
                initial_val = float(entry_value.get())
                slider.set(initial_val)
            except (ValueError, tk.TclError):
                slider.set(min_val)
            # --- Layout Refactor: End ---

            def on_slider_move(val):
                entry_value.set(f"{float(val):.2f}")

            def on_entry_change(event):
                try:
                    new_val = float(entry.get())
                    if min_val <= new_val <= max_val:
                        slider.set(new_val)
                except ValueError:
                    matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "Invalid input, please enter a number.", level="DEBUG")

            slider.config(command=on_slider_move)
            entry.bind("<FocusOut>", on_entry_change)
            entry.bind("<Return>", on_entry_change)

            # --- New Logic: Trace for external updates ---
            def _update_slider_from_entry_var(*args):
                if not entry_value.get():  # Check for empty string
                    matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "Empty string in entry_value for slider. Ignoring update.", level="DEBUG")
                    return  # Exit early if the string is empty

                try:
                    new_val = float(entry_value.get())
                    # Ensure the value is within the slider's range before setting
                    if min_val <= new_val <= max_val:
                        slider.set(new_val)
                    elif new_val < min_val:
                        slider.set(min_val)
                    elif new_val > max_val:
                        slider.set(max_val)
                except (ValueError, tk.TclError):
                    # Handle cases where entry_value might not be a valid float
                    matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"Invalid value in entry_value for slider: {entry_value.get()}", level="DEBUG")

            # Bind the trace to the entry_value
            entry_value.trace_add("write", _update_slider_from_entry_var)

            if path:
                if hasattr(builder_instance, "topic_widgets"):
                    builder_instance.topic_widgets[path] = (entry_value, slider)

                # --- New MQTT Wiring ---
                widget_id = path

                # 1. Register widget
                topic = state_mirror_engine.register_widget(
                    widget_id, entry_value, base_mqtt_topic_from_path, config_data
                )

                # 2. Bind variable trace for outgoing messages
                callback = lambda: state_mirror_engine.broadcast_gui_change_to_mqtt(
                    widget_id
                )
                bind_variable_trace(entry_value, callback)

                # 3. Subscribe to topic for incoming messages
                if subscriber_router and topic:
                    subscriber_router.subscribe_to_topic(
                        topic, state_mirror_engine.sync_incoming_mqtt_to_gui
                    )

                # 4. Initialize the widget state from cache or broadcast initial state
                state_mirror_engine.initialize_widget_state(widget_id)

            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"✅ SUCCESS! The slider '{label}' has materialized!", level="SUCCESS")
            return sub_frame

        except Exception as e:
            logger.exception("💥 KABOOM! The slider contraption for '{label}' has malfunctioned! Error")
            return None