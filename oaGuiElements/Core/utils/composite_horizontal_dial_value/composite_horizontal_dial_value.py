# composite_horizontal_dial_value/composite_horizontal_dial_value.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized Composite Horizontal Fader & Dial.

import tkinter as tk
from tkinter import ttk
from loguru import logger

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True
from oaLogging.Core.logger import builder_logger
from oaConfiguration.FileReaders.config_reader import Config
app_constants = Config.get_instance()

from oaOchestration.Methods.widget_event_binder import bind_variable_trace
from oaGuiManager.Core.context.widget_context import WidgetContext
from oaGuiElements.Core.faders.fader_horizontal.fader_horizontal import BuilderFaderHorizontalCreator
from oaGuiElements.Core.utils.knob.knob import BuilderKnobCreator
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
from oaGuiManager.Core.transparency.transparency import TransparencyManager
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry

# --- EXTRACTED CORE MODULES ---
from .Core.grid import GridManager
from .Core.state_sync import CompositeStateSync
from .Core.ui_components import CompositeUIComponents

@WidgetRegistry.register("_Horizontal_with_dial_Value", "OcaCompositeFaderKnob")
class BuilderCompositeHorizontalDialValueCreator(
    BuilderFaderHorizontalCreator, BuilderKnobCreator, TransparencyMixin
):
    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        """Unified entry point for composite horizontal dial value."""
        creator = BuilderCompositeHorizontalDialValueCreator()
        return creator.make_composite_horizontal_dial_value(parent_widget, config_data, context, **kwargs)

    def make_composite_horizontal_dial_value(self, parent_widget, config_data, context=None, **kwargs):
        if BUILDER_DEBUG: builder_logger.trace(f"🔬🏗️🔀 [BUILDER] Creating composite horizontal dial value.")
        
        label, path = config_data.get("label_active", config_data.get("label", "Composite")), config_data.get("path", "")
        
        # Context extraction
        if context:
            state_mirror_engine, subscriber_router, base_mqtt_topic = context.state_mirror_engine, context.subscriber_router, context.base_mqtt_topic_from_path
            builder_instance = context.builder_instance
        else:
            state_mirror_engine = getattr(self, 'state_mirror_engine', None)
            subscriber_router = getattr(self, 'subscriber_router', None)
            base_mqtt_topic = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance") or self
            context = WidgetContext(state_mirror_engine=state_mirror_engine, subscriber_router=subscriber_router, base_mqtt_topic_from_path=base_mqtt_topic, app_instance=getattr(self, 'app_instance', None), builder_instance=builder_instance, on_focus_widget=getattr(self, 'on_focus_widget', None))

        try:
            p_bg = parent_widget.cget("bg") if hasattr(parent_widget, 'cget') and parent_widget.cget("bg").startswith("#") else "#2b2b2b"

            # 1. Container Setup
            l_cfg = config_data.get("layout", {})
            w_req, h_req = int(float(config_data.get("width", l_cfg.get("width", 400)))), int(float(config_data.get("height", l_cfg.get("height", 100))))

            sub_frame = tk.Canvas(parent_widget, bd=0, highlightthickness=0, relief="flat", bg=p_bg, width=w_req, height=h_req)
            sub_frame._oca_path = path; sub_frame.grid_propagate(False)
            TransparencyManager.apply_transparency(sub_frame, sub_frame, config_data, builder_instance)

            safe_knob_dim, v_width_limit = GridManager.configure(sub_frame, config_data, w_req)

            # 2. Config Parsing
            min_val, max_val = float(config_data.get("min", "0")), float(config_data.get("max", "100"))
            step_coarse, step_fine = float(config_data.get("step_coarse", "1.0")), float(config_data.get("step_fine", config_data.get("step", "0.01")))
            numerical_step = step_fine
            fmt_str = CompositeStateSync.get_format_string(numerical_step)

            init_val = float(config_data.get("default_value", config_data.get("value", "0")))
            main_value_var, entry_string_var = tk.DoubleVar(value=init_val), tk.StringVar(value=fmt_str.format(init_val))

            v_cfg = config_data.get("value_config", {}).copy()
            v_font_size = int(float(v_cfg.get("font", v_cfg.get("font_size", 9))))
            v_text_color = v_cfg.get("colour", v_cfg.get("text_color", "#ffffff"))
            v_width = max(3, min(int(float(v_cfg.get("width", 6))), v_width_limit))

            # 3. Component Creation
            ui_ctx = {
                'sub_frame': sub_frame, 'p_bg': p_bg, 'trans_mgr': TransparencyManager,
                'builder_instance': builder_instance, 'config_data': config_data,
                'label_text': label, 'path': path, 'v_width': v_width,
                'v_font_size': v_font_size, 'v_text_color': v_text_color,
                'entry_string_var': entry_string_var, 'on_manual_cb': None,
                'units_txt': config_data.get("units", "")
            }

            f_label, draw_f_label = CompositeUIComponents.build_label(ui_ctx)

            # Fader
            f_cfg = config_data.copy()
            f_cfg.update(config_data.get("fader_config", {}))
            f_cfg.update({"value_min": str(min_val), "value_max": str(max_val), "value_default": str(init_val), "label_active": "", "show_label": False, "tick_interval": f_cfg.get("tick_interval", step_coarse), "path": f"{path}.fader_config" if "fader_config" in config_data else path, "width": w_req * 0.8 if w_req > 0 else 320, "height": h_req * 0.7 if h_req > 0 else 70, "cap_height": f_cfg.get("cap_height", 55)})
            fader_widget = self.make_fader_horizontal(sub_frame, f_cfg, context=context)
            fader_widget.grid(row=1, column=0, sticky="nsew", padx=(5, 0), pady=(0, 5)); fader_widget._oca_path = f_cfg["path"]

            # Dial
            d_cfg = config_data.copy()
            d_cfg.update(config_data.get("dial_config", {}))
            d_cfg.update({"label_active": "", "show_label": False, "min": "0", "max": "999", "knob_style": d_cfg.get("knob_style", "dial"), "path": f"{path}.dial_config" if "dial_config" in config_data else path, "width": safe_knob_dim, "height": safe_knob_dim})
            dial_widget = self.make_knob(sub_frame, d_cfg, context=context)
            dial_widget.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=5); dial_widget._oca_path = d_cfg["path"]

            def on_manual(e):
                try: 
                    val = round(float(entry_string_var.get()) / numerical_step) * numerical_step
                    main_value_var.set(max(min_val, min(max_val, val)))
                except: entry_string_var.set(fmt_str.format(main_value_var.get()))

            ui_ctx['on_manual_cb'] = on_manual
            val_container, entry, sync_entry_style = CompositeUIComponents.build_entry(ui_ctx)
            unit_label, draw_unit_label = CompositeUIComponents.build_unit_label(ui_ctx)

            # 4. State Synchronization
            dial_widget._prev_dial_val_for_wrap_detection = CompositeStateSync.calculate_initial_fine(init_val, step_coarse, numerical_step)

            def update_from_main(*args): CompositeStateSync.sync_from_main(main_value_var.get(), step_coarse, numerical_step, fmt_str, entry_string_var, fader_widget.variable, dial_widget)
            def on_f_change(*args): main_value_var.set(CompositeStateSync.calc_from_fader(fader_widget.variable.get(), main_value_var.get(), step_coarse, numerical_step, min_val, max_val))
            def on_d_change(*args):
                ctx = {
                    'curr_dial': dial_widget.variable.get(), 'main_val': main_value_var.get(),
                    'fader_var': fader_widget.variable, 'dial_widget': dial_widget,
                    'step_coarse': step_coarse, 'numerical_step': numerical_step,
                    'min_val': min_val, 'max_val': max_val
                }
                main_value_var.set(CompositeStateSync.calc_from_dial(ctx))

            fader_widget.variable.trace_add("write", on_f_change)
            dial_widget.variable.trace_add("write", on_d_change)
            main_value_var.trace_add("write", update_from_main)

            def sync_bg():
                sync_entry_style(); draw_f_label(); draw_unit_label()
                if hasattr(fader_widget, "render"): fader_widget.render()
                if hasattr(dial_widget, "render"): dial_widget.render()
            
            sub_frame.render = sub_frame._draw = sync_bg
            update_from_main()

            if path:
                topic = state_mirror_engine.register_widget(path, main_value_var, base_mqtt_topic, config_data)
                bind_variable_trace(main_value_var, lambda: state_mirror_engine.broadcast_gui_change_to_mqtt(path))
                if subscriber_router and topic: subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
                state_mirror_engine.initialize_widget_state(path)

            return sub_frame
        except Exception as e:
            if BUILDER_DEBUG: logger.exception(f"❌🚫🛑 [ERROR] Critical failure creating composite '{label}'")
            return None

    def make_knob(self, parent_widget, config_data, context=None, **kwargs):
        return BuilderKnobCreator.make(parent_widget, config_data, context, builder_instance=kwargs.pop('builder_instance', self), **kwargs)
