# slider_value/slider_value.py
from oaGui.Methods.i18n_utils import get_text
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
from oaComProtocols.oaComMQTT.Methods.mqtt_topic_utils import get_topic
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin


# --- Global Scope Variables ---
current_file = f"{os.path.basename(__file__)}"

# --- Constants ---
DEFAULT_PAD_X = 5
DEFAULT_PAD_Y = 2


from oaGuiBuilder.Core.base_widget_creator import BaseWidgetCreator

class BuilderSliderValueCreator(BaseWidgetCreator, TransparencyMixin):
    """
    A mixin class that provides the functionality for creating a
    slider widget combined with a text entry box.
    """
    
    is_composite = True

    def __init__(self):
        self.topic_widgets = {}

    def _assemble_ui(self, parent_widget, config_data, context, **kwargs):
        """Assembles the Slider Value UI."""
        # Creates a slider and an entry box for a numerical value.
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬 Entering _assemble_ui with config: {config_data}", level="TRACE")

        # Extract only widget-specific config from config_data
        label = config_data.get("label_active", "")
        path = config_data.get("path")

        ctx = context if context else type('obj', (object,), kwargs)()
        b_inst = getattr(ctx, 'builder_instance', None) or getattr(ctx, 'app_instance', None) or kwargs.get('builder_instance')
        s_engine = getattr(ctx, 'state_mirror_engine', None) or kwargs.get('state_mirror_engine')
        s_router = getattr(ctx, 'subscriber_router', None) or kwargs.get('subscriber_router')
        b_topic = getattr(ctx, 'base_mqtt_topic_from_path', None) or kwargs.get('base_mqtt_topic_from_path', "")

        try:
            sub_frame = tk.Frame(parent_widget, bd=0, highlightthickness=0, relief="flat")
            
            # Apply Industrial Transparency
            if hasattr(b_inst, '_apply_transparency'):
                b_inst._apply_transparency(sub_frame, None, config_data, b_inst)

            layout_config = config_data.get("layout", {})
            font_size = layout_config.get("font", 12)
            custom_font = ("Helvetica", font_size)

            # --- Layout Refactor: Start ---
            # Line 1: Label, Textbox, Units
            top_info_frame = tk.Canvas(sub_frame, bd=0, highlightthickness=0, relief="flat", height=30)
            top_info_frame.pack(side=tk.TOP, fill=tk.X, expand=True)
            
            # Apply Industrial Transparency to internal frames
            if hasattr(b_inst, '_apply_transparency'):
                b_inst._apply_transparency(top_info_frame, top_info_frame, config_data, b_inst)

            top_info_frame._last_redraw_size = (0, 0)

            def redraw_labels(*args):
                if not top_info_frame.winfo_exists(): return
                w = top_info_frame.winfo_width()
                h = top_info_frame.winfo_height()
                if (w, h) == top_info_frame._last_redraw_size: return
                if w <= 1: return
                top_info_frame._last_redraw_size = (w, h)
                
                top_info_frame.delete("industrial_text")
                top_info_frame.create_text(5, h/2, text=f"{label}:", anchor="w", fill="white", font=custom_font, tags="industrial_text")
                units_txt = config_data.get("units", "")
                top_info_frame.create_text(w-5, h/2, text=units_txt, anchor="e", fill="white", font=custom_font, tags="industrial_text")

            top_info_frame.bind("<Configure>", redraw_labels, add="+")

            entry_value = tk.StringVar(value=config_data.get("value", "0"))
            entry = ttk.Entry(top_info_frame, width=7, style="Custom.TEntry", textvariable=entry_value, justify=tk.RIGHT, font=custom_font)
            u_txt = config_data.get("units", "")
            u_pad = 60 if u_txt else 5
            entry.pack(side=tk.RIGHT, padx=(DEFAULT_PAD_X, u_pad))

            sub_frame._draw = lambda: redraw_labels()
            min_val = float(config_data.get("min", "0"))
            max_val = float(config_data.get("max", "100"))

            style = ttk.Style(sub_frame)
            style_name = f"Thicker.{font_size}.Horizontal.TScale"
            style.configure(style_name, sliderlength=font_size * 2)
            slider = ttk.Scale(sub_frame, from_=min_val, to=max_val, orient=tk.HORIZONTAL, style=style_name)
            slider.pack(side=tk.TOP, fill=tk.X, expand=True, padx=DEFAULT_PAD_X, pady=(0, DEFAULT_PAD_Y))

            try:
                initial_val = float(entry_value.get())
                slider.set(initial_val)
            except (ValueError, tk.TclError):
                slider.set(min_val)

            def on_slider_move(value): entry_value.set(f"{float(value):.2f}")
            def on_entry_change(event):
                try:
                    new_val = float(entry.get())
                    if min_val <= new_val <= max_val: slider.set(new_val)
                except ValueError: pass

            slider.config(command=on_slider_move)
            entry.bind("<FocusOut>", on_entry_change)
            entry.bind("<Return>", on_entry_change)

            def _update_slider_from_entry_var(*args):
                try:
                    if not entry_value.get(): return
                    new_val = float(entry_value.get())
                    slider.set(max(min_val, min(max_val, new_val)))
                except: pass

            entry_value.trace_add("write", _update_slider_from_entry_var)

            if path and s_engine:
                topic = s_engine.register_widget(path, entry_value, b_topic, config_data)
                bind_variable_trace(entry_value, lambda: s_engine.broadcast_gui_change_to_mqtt(path))
                if s_router and topic:
                    s_router.subscribe_to_topic(topic, s_engine.sync_incoming_mqtt_to_gui)
                s_engine.initialize_widget_state(path)

            return sub_frame, sub_frame

        except Exception as e:
            logger.exception(f"💥 failure in slider for '{label}'")
            return None, None

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        return BuilderSliderValueCreator.build(parent_widget, config_data, context, **kwargs)

    def make_slider_value(self, parent_widget, config_data, context=None, **kwargs):
        return self.build(parent_widget, config_data, context, **kwargs)