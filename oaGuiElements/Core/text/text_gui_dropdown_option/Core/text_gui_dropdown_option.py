# text_gui_dropdown_option/text_gui_dropdown_option.py
from oaGui.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized dynamic Text Dropdown (Combobox).

import tkinter as tk
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
from tkinter import ttk
from loguru import logger

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False
from oaLogging.Core.logger import builder_logger
from oaConfigurationManager.FileReaders.config_reader import Config
app_constants = Config.get_instance()

from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
from oaGuiManager.Core.transparency.transparency import TransparencyManager
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry

# --- EXTRACTED CORE MODULES ---
from ..dropdown_style_mixin import DropdownStyleMixin
from ..dropdown import DropdownDataManager

@WidgetRegistry.register("_GuiDropDownOption")
class BuilderTextGuiDropdownOptionCreator(TransparencyMixin):
    """A mixin class providing functionality for creating a dropdown (Combobox) widget."""

    def make_text_gui_dropdown_option(self, parent_widget, config_data, context=None, **kwargs):
        label, path = get_text(config_data.get("label")), config_data.get("path")

        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic = context.base_mqtt_topic_from_path
            builder_instance = context.builder_instance
        else:
            state_mirror_engine = kwargs.get("state_mirror_engine")
            subscriber_router = kwargs.get("subscriber_router")
            base_mqtt_topic = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance") or self

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🧪🏗️🖥️ Dropdown for '{label}'...", level="DEBUG")

        try:
            sub_frame = tk.Canvas(parent_widget, bd=0, highlightthickness=0, relief="flat", height=30)
            if hasattr(self, '_apply_transparency'):
                TransparencyManager.apply_transparency(sub_frame, sub_frame, config_data, builder_instance)

            # 1. Data parsing
            options_map, option_labels, option_values = DropdownDataManager.parse_options(config_data)
            init_val, init_label = DropdownDataManager.determine_initial_state(config_data, options_map, option_values)
            
            selected_value_var = tk.StringVar(value=init_val)
            displayed_text_var = tk.StringVar(value=init_label)

            # 2. Sync Logic
            def update_display(*args):
                nv = selected_value_var.get(); fl = ""
                for k, opt in options_map.items():
                    if str(opt.get("value", k)) == str(nv):
                        fl = DropdownDataManager.get_display_label(opt, k); break
                displayed_text_var.set(fl)
            selected_value_var.trace_add("write", update_display)

            def on_select(event):
                try:
                    sl = displayed_text_var.get()
                    sk = next((k for k, opt in options_map.items() if DropdownDataManager.get_display_label(opt, k) == sl), None)
                    if sk:
                        sv = options_map.get(sk, {}).get("value", sk)
                        if selected_value_var.get() != str(sv): selected_value_var.set(sv)
                        if state_mirror_engine: state_mirror_engine.broadcast_gui_change_to_mqtt(path)
                except ValueError: logger.error("❌ Invalid dropdown selection.")

            # 3. Styling & UI
            style_name = f"Dropdown.{path.replace('/', '_') if path else 'default'}.TCombobox"
            
            dropdown = ttk.Combobox(sub_frame, textvariable=displayed_text_var, values=option_labels, state="readonly", style=style_name)
            dropdown.bind("<<ComboboxSelected>>", on_select)
            dropdown.pack(side=tk.LEFT, padx=(80 if label else 10, 5))

            def redraw_label(*args):
                if not sub_frame.winfo_exists() or sub_frame.winfo_width() <= 1: return
                sub_frame.delete("industrial_text")
                if label: sub_frame.create_text(10, sub_frame.winfo_height()/2, text=f"{label}:", anchor="w", fill="white", font=("Helvetica", 9), tags="industrial_text")

            def sync_bg():
                bg = sub_frame.cget("bg")
                DropdownStyleMixin.apply_style(style_name, bg)
                redraw_label()
            
            sub_frame._draw = sub_frame.render = sync_bg
            sub_frame.bind("<Configure>", redraw_label, add="+")

            # 4. MQTT Integration
            if path and state_mirror_engine:
                topic = state_mirror_engine.register_widget(path, selected_value_var, base_mqtt_topic, config_data)
                if topic and subscriber_router: subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
                state_mirror_engine.initialize_widget_state(path)
            
            return sub_frame
        except Exception as e:
            if LOCAL_DEBUG: logger.exception(f"❌ Error in Dropdown creation for '{label}'")
            return None

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        creator = BuilderTextGuiDropdownOptionCreator()
        return creator.make_text_gui_dropdown_option(parent_widget, config_data, context, **kwargs)