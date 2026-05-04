# composite_horizontal_dial_value/composite_horizontal_dial_value.py
import inspect

# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized Composite Horizontal Fader & Dial.
import tkinter as tk

from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config
from oaGui.Methods.formatting.i18n_utils import get_text

# --- Standard Debug Logging Setup ---
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()

from oaGui.Core.factory.base_widget_creator import BaseWidgetCreator
from oaGuiElements.Core.faders.fader_horizontal.Core.fader_horizontal import BuilderFaderHorizontalCreator
from oaGuiElements.Core.Knobs.knob.Core.knob import BuilderKnobCreator
from oaGui.Hooks.registry.registry_widget_store import RegistryWidgetStore
from oaGui.Workers.compositing.engine_visual_effects import EngineVisualEffects
from oaGui.Workers.compositing.sync_behavior import SyncBehavior

# --- Standard Debug Logging Setup ---
from oaLogging.Methods.matrix_gate import is_debug_allowed

# --- EXTRACTED CORE MODULES ---
from .grid import GridManager
from .state_sync import CompositeStateSync
from .ui_components import CompositeUIComponents

BUILDER_DEBUG = is_debug_allowed(system="UI", element="GUI_BUILDER")

@RegistryWidgetStore.register("_Horizontal_with_dial_Value", "OcaCompositeFaderKnob")
class BuilderCompositeHorizontalDialValueCreator(
    BaseWidgetCreator, SyncBehavior
):
    is_composite = True

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        """Unified entry point for composite horizontal dial value."""
        return BuilderCompositeHorizontalDialValueCreator.build(parent_widget, config_data, context, **kwargs)

    def _assemble_ui(self, parent_widget, config_data, context, **kwargs):
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🔬🏗️🔀 [BUILDER] Creating composite horizontal dial value.", level="TRACE")

        label, path = get_text(config_data.get("label_active"), get_text(config_data.get("label"), "Composite")), config_data.get("path", "")

        # Context extraction
        state_mirror_engine = getattr(context, 'state_mirror_engine', None)
        subscriber_router = getattr(context, 'subscriber_router', None)
        base_mqtt_topic = getattr(context, 'base_mqtt_topic_from_path', None)
        builder_instance = getattr(context, 'builder_instance', None)

        try:
            p_bg = parent_widget.cget("bg") if hasattr(parent_widget, 'cget') and parent_widget.cget("bg").startswith("#") else "#2b2b2b"

            # 1. Container Setup
            l_cfg = config_data.get("layout", {})
            w_req, h_req = int(float(config_data.get("width", l_cfg.get("width", 400)))), int(float(config_data.get("height", l_cfg.get("height", 100))))

            sub_frame = tk.Canvas(parent_widget, bd=0, highlightthickness=0, relief="flat", bg=p_bg, width=w_req, height=h_req)
            sub_frame._oca_path = path

            # ⚡ PROPAGATION SAFETY: If we are in ghost/preview mode, we MUST propagate
            # otherwise the container collapses to 1x1 if width/height were stripped.
            render_tier = getattr(builder_instance, '_render_tier', 'high_res')
            if render_tier in ['ghost', 'fast'] or not (w_req and h_req):
                sub_frame.grid_propagate(True)
            else:
                sub_frame.grid_propagate(False)

            EngineVisualEffects.apply_transparency(sub_frame, sub_frame, config_data, builder_instance)

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
                'sub_frame': sub_frame, 'p_bg': p_bg, 'trans_mgr': EngineVisualEffects,
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
                    value = round(float(entry_string_var.get()) / numerical_step) * numerical_step
                    main_value_var.set(max(min_val, min(max_val, value)))
                except: entry_string_var.set(fmt_str.format(main_value_var.get()))

            ui_ctx['on_manual_cb'] = on_manual
            val_container, entry, sync_entry_style = CompositeUIComponents.build_entry(ui_ctx)
            unit_label, draw_unit_label = CompositeUIComponents.build_unit_label(ui_ctx)

            # 4. State Synchronization
            # ⚡ GHOST AWARENESS: Only wire up synchronization if sub-widgets are fully functional (have .variable)
            is_ghost = not hasattr(fader_widget, 'variable') or not hasattr(dial_widget, 'variable')

            if not is_ghost:
                dial_widget._prev_dial_val_for_wrap_detection = CompositeStateSync.calculate_initial_fine(init_val, step_coarse, numerical_step)

                def update_from_main(*args): CompositeStateSync.sync_from_main(main_value_var.get(), step_coarse, numerical_step, fmt_str, entry_string_var, fader_widget.variable, dial_widget)
                def on_f_change(*args): main_value_var.set(CompositeStateSync.calc_from_fader(fader_widget.variable.get(), main_value_var.get(), step_coarse, numerical_step, min_val, max_val))
                def on_d_change(*args):
                    sync_ctx = {
                        'curr_dial': dial_widget.variable.get(), 'main_val': main_value_var.get(),
                        'fader_var': fader_widget.variable, 'dial_widget': dial_widget,
                        'step_coarse': step_coarse, 'numerical_step': numerical_step,
                        'min_val': min_val, 'max_val': max_val
                    }
                    main_value_var.set(CompositeStateSync.calc_from_dial(sync_ctx))

                fader_widget.variable.trace_add("write", on_f_change)
                dial_widget.variable.trace_add("write", on_d_change)
                main_value_var.trace_add("write", update_from_main)
                update_from_main()

            def sync_bg():
                sync_entry_style(); draw_f_label(); draw_unit_label()
                if hasattr(fader_widget, "render"): fader_widget.render()
                if hasattr(dial_widget, "render"): dial_widget.render()

            sub_frame.render = sub_frame._draw = sync_bg

            sub_frame.variable = main_value_var
            return sub_frame, sub_frame
        except Exception:
            if BUILDER_DEBUG: logger.exception(f"❌🚫🛑 [ERROR] Critical failure creating composite '{label}'")
            return None, None

    def make_knob(self, parent_widget, config_data, context=None, **kwargs):
        """Internal factory call for knob component."""
        return BuilderKnobCreator.build(parent_widget, config_data, context=context, **kwargs)

    def make_fader_horizontal(self, parent_widget, config_data, context=None, **kwargs):
        """Internal factory call for fader component."""
        return BuilderFaderHorizontalCreator.build(parent_widget, config_data, context=context, **kwargs)
