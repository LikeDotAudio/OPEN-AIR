# composite_horizontal_dial_value/composite_horizontal_dial_value.py
#
# A composite widget providing a horizontal fader and a dial for coarse/fine control.
# Refactored for a grid-based 3-column architecture:
# Column 0: Label (Row 0), Horizontal Fader (Row 1) (60%)
# Column 1: Knob (Span Rows 0-1) (20%)
# Column 2: Value Entry (Row 0), Units (Row 1) (20%)
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20260307.Grid.4

import tkinter as tk
from tkinter import ttk
import math

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True
from workers.logger.logger import builder_logger
from loguru import logger

from managers.configini.config_reader import Config
app_constants = Config.get_instance()

from workers.handlers.widget_event_binder import bind_variable_trace
from managers.Display.context.widget_context import WidgetContext
from workers.builder.fader_horizontal.fader_horizontal import BuilderFaderHorizontalCreator
from workers.builder.knob.knob import BuilderKnobCreator
from managers.Display.transparency.transparency_mixin import TransparencyMixin
from managers.Display.transparency.transparency_manager import TransparencyManager
from managers.Display.factory.widget_registry import WidgetRegistry

@WidgetRegistry.register("_Horizontal_with_dial_Value", "OcaCompositeFaderKnob")
class BuilderCompositeHorizontalDialValueCreator(
    BuilderFaderHorizontalCreator, BuilderKnobCreator, TransparencyMixin
):
    @staticmethod
    def _get_format_string(step):
        step = float(step)
        if step == 0: return "{}"
        if step == int(step): return "{:.0f}"
        try: decimal_places = len(str(float(step)).split('.')[-1])
        except: decimal_places = 2
        return f"{{:.{decimal_places}f}}"

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        """Static factory method for creating the composite widget."""
        creator = BuilderCompositeHorizontalDialValueCreator()
        return creator.make_composite_horizontal_dial_value(parent_widget, config_data, context, **kwargs)

    def make_composite_horizontal_dial_value(self, parent_widget, config_data, context=None, **kwargs):
        """Creates a composite horizontal fader and dial widget with 3-column grid layout."""
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️🔀 [BUILDER] Entering make_composite_horizontal_dial_value")
        
        label = config_data.get("label_active") or config_data.get("label", "Composite")
        path = config_data.get("path", "")
        
        # ⚡ HARDENED INTERFACE: Extract from context if available
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            builder_instance = context.builder_instance
        else:
            state_mirror_engine = getattr(self, 'state_mirror_engine', None)
            subscriber_router = getattr(self, 'subscriber_router', None)
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance") or self
            context = WidgetContext(
                state_mirror_engine=state_mirror_engine,
                subscriber_router=subscriber_router,
                base_mqtt_topic_from_path=base_mqtt_topic_from_path,
                app_instance=getattr(self, 'app_instance', None),
                builder_instance=builder_instance,
                on_focus_widget=getattr(self, 'on_focus_widget', None)
            )

        try:
            p_bg = "#2b2b2b"
            try:
                p_bg = parent_widget.cget("bg")
                if not p_bg or not p_bg.startswith("#"): p_bg = "#2b2b2b"
            except: pass

            # ⚡ CONTAINER: Use tk.Canvas for transparency support
            # Use requested dimensions, but allow expansion
            l_cfg = config_data.get("layout", {})
            w_req = int(float(config_data.get("width", l_cfg.get("width", 400))))
            h_req = int(float(config_data.get("height", l_cfg.get("height", 100))))

            sub_frame = tk.Canvas(parent_widget, bd=0, highlightthickness=0, relief="flat", bg=p_bg, width=w_req, height=h_req)
            sub_frame._oca_path = path # ⚡ MANDATORY: For WYSIWYG selection
            sub_frame.grid_propagate(False) # ⚡ STRICT: Force columns to respect weights
            
            # Apply Industrial Transparency to the container
            TransparencyManager.apply_transparency(sub_frame, sub_frame, config_data, builder_instance)

            # --- Grid Configuration (Default 80/10/10 Spacing) ---
            spacing = config_data.get("column_spacing", [80, 10, 10])
            if not isinstance(spacing, list) or len(spacing) < 3:
                spacing = [80, 10, 10]

            # ⚡ UNIFORM: Using 'col' group forces columns to respect weights
            # We use weight=int(spacing[i]) to ensure they scale exactly as requested
            sub_frame.grid_columnconfigure(0, weight=int(spacing[0]), uniform="col")
            sub_frame.grid_columnconfigure(1, weight=int(spacing[1]), uniform="col")
            sub_frame.grid_columnconfigure(2, weight=int(spacing[2]), uniform="col")

            # ⚡ ROW WEIGHTS: Vertical distribution (Title vs Control)
            sub_frame.grid_rowconfigure(0, weight=3, minsize=25) # Top row (Label/Entry)
            sub_frame.grid_rowconfigure(1, weight=7, minsize=50) # Bottom row (Fader/Units)


            # ⚡ DYNAMIC SIZING: Calculate sub-widget limits based on requested 10% columns
            col_1_w = (w_req * spacing[1]) / sum(spacing)
            col_2_w = (w_req * spacing[2]) / sum(spacing)
            
            # Knob should be slightly smaller than its column width to avoid clipping
            safe_knob_dim = int(col_1_w * 0.9) if col_1_w > 0 else 40
            safe_knob_dim = max(30, min(100, safe_knob_dim)) # Clamp to reasonable range

            min_val = float(config_data.get("min", "0"))
            max_val = float(config_data.get("max", "100"))
            step_coarse = float(config_data.get("step_coarse", "1.0"))
            step_fine = float(config_data.get("step_fine", config_data.get("step", "0.01")))
            numerical_step = step_fine
            format_string = self._get_format_string(numerical_step)

            initial_value = float(config_data.get("default_value", config_data.get("value", "0")))
            main_value_var = tk.DoubleVar(value=initial_value)
            entry_string_var = tk.StringVar(value=format_string.format(initial_value))

            v_cfg = config_data.get("value_config", {}).copy()
            v_font_size = int(float(v_cfg.get("font", v_cfg.get("font_size", 9))))
            v_text_color = v_cfg.get("colour", v_cfg.get("text_color", "#ffffff"))
            
            # ⚡ SMART ENTRY WIDTH: Cap based on 10% column space
            # Average char width is ~7-8px. For a 40-60px col, we need 4-6 chars.
            v_width_limit = int(col_2_w / 8) - 1 if col_2_w > 0 else 8
            v_width = int(float(v_cfg.get("width", 6)))
            v_width = max(3, min(v_width, v_width_limit))

            # --- COLUMN 0: LABEL & FADER ---
            # Row 0: Label
            f_label = tk.Canvas(sub_frame, bd=0, highlightthickness=0, height=25, bg=p_bg)
            f_label.grid(row=0, column=0, sticky="nsew", padx=5)
            TransparencyManager.apply_transparency(f_label, f_label, config_data, builder_instance)
            
            def draw_f_label(e=None):
                if not f_label.winfo_exists(): return
                f_label.delete("all")
                f_label.create_text(5, 23, text=label.upper(), fill="#888888", font=("Helvetica", 8, "bold"), anchor="sw")
            f_label.bind("<Configure>", draw_f_label)

            # Row 1: Fader
            f_config_exists = "fader_config" in config_data
            f_config = config_data.copy()
            if f_config_exists: 
                f_config.update(config_data["fader_config"])
            
            f_config.update({
                "value_min": str(min_val), "value_max": str(max_val),
                "value_default": str(initial_value), 
                "label_active": "", # We draw our own label
                "show_label": False,
                "tick_interval": f_config.get("tick_interval", step_coarse),
                "path": f"{path}.fader_config" if f_config_exists else path, # ⚡ PATH: Sub-path for selection
                "width": w_req * 0.8 if w_req > 0 else 320,
                "height": h_req * 0.7 if h_req > 0 else 70,
                "cap_height": f_config.get("cap_height", 55) # ⚡ EVEN LARGER CAP
            })
            fader_widget = self.make_fader_horizontal(sub_frame, f_config, context=context)
            fader_widget.grid(row=1, column=0, sticky="nsew", padx=(5, 0), pady=(0, 5))
            fader_widget._oca_path = f_config["path"] # ⚡ FOR EDITOR

            # --- COLUMN 1: KNOB (Spans both rows) ---
            d_config_exists = "dial_config" in config_data
            d_config = config_data.copy()
            if d_config_exists: 
                d_config.update(config_data["dial_config"])

            d_config.update({
                "label_active": "", "show_label": False, "min": "0", "max": "999", 
                "knob_style": d_config.get("knob_style", "dial"), 
                "path": f"{path}.dial_config" if d_config_exists else path # ⚡ PATH: Sub-path for selection
            })
            # Remove fixed widths, let grid weights rule, use calculated safe dim
            d_config["width"] = int(float(d_config.get("width", safe_knob_dim)))
            d_config["height"] = int(float(d_config.get("height", safe_knob_dim)))

            dial_widget = self.make_knob(sub_frame, d_config, context=context)
            dial_widget.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=5)
            dial_widget._oca_path = d_config["path"] # ⚡ FOR EDITOR

            # --- COLUMN 2: VALUE & UNITS ---
            # Row 0: Value Entry
            v_config_exists = "value_config" in config_data
            val_container = tk.Canvas(sub_frame, bd=0, highlightthickness=0, height=35, bg=p_bg)
            val_container.grid(row=0, column=2, sticky="nsew", padx=5)
            val_container._oca_path = f"{path}.value_config" if v_config_exists else path
            TransparencyManager.apply_transparency(val_container, val_container, config_data, builder_instance)

            clean_path = path.replace('/', '_') if path else "default"
            style_name = f"CompVal.{clean_path}.TEntry"
            style = ttk.Style()
            
            def sync_entry_style():
                if not val_container.winfo_exists(): return
                bg = val_container.cget("bg")
                style.configure(style_name, fieldbackground=bg, foreground=v_text_color, insertcolor="white", font=("Helvetica", v_font_size))

            entry = ttk.Entry(val_container, width=v_width, style=style_name, textvariable=entry_string_var, justify=tk.CENTER)
            entry.place(relx=0.5, rely=0.5, anchor="center")

            # Row 1: Units
            unit_label = tk.Canvas(sub_frame, bd=0, highlightthickness=0, height=25, bg=p_bg)
            unit_label.grid(row=1, column=2, sticky="nsew", padx=5)
            TransparencyManager.apply_transparency(unit_label, unit_label, config_data, builder_instance)
            
            def draw_unit_label(e=None):
                if not unit_label.winfo_exists(): return
                unit_label.delete("all")
                units_txt = config_data.get("units", "")
                unit_label.create_text(unit_label.winfo_width()/2, 5, text=units_txt, fill="#888888", font=("Helvetica", v_font_size-1), anchor="n")
            unit_label.bind("<Configure>", draw_unit_label)

            # --- Logic & Sync ---
            scaled_initial_fine = 0.0
            if numerical_step < step_coarse:
                fine_part = initial_value % step_coarse
                eff_range = step_coarse - numerical_step if (step_coarse - numerical_step) > 0 else step_coarse
                scaled_initial_fine = (fine_part / eff_range) * 999.0
            dial_widget._prev_dial_val_for_wrap_detection = round(scaled_initial_fine)

            def update_widgets_from_main_var(*args):
                try:
                    val = main_value_var.get()
                    entry_string_var.set(format_string.format(val))
                    coarse_val = math.floor(val / step_coarse) * step_coarse
                    fader_widget.variable.set(coarse_val)
                    if numerical_step < step_coarse:
                        fine_part = val % step_coarse
                        eff_range = step_coarse - numerical_step if (step_coarse - numerical_step) > 0 else step_coarse
                        dial_disp = (fine_part / eff_range) * 999.0
                        dial_widget.variable.set(round(dial_disp))
                        dial_widget._prev_dial_val_for_wrap_detection = round(dial_disp)
                    else: dial_widget.variable.set(0)
                except: pass

            def on_fader_change(*args):
                try:
                    f_val = round(fader_widget.variable.get() / step_coarse) * step_coarse
                    fine = main_value_var.get() % step_coarse if numerical_step < step_coarse else 0
                    new_val = round((f_val + fine) / numerical_step) * numerical_step
                    main_value_var.set(max(min_val, min(max_val, new_val)))
                except: pass

            def on_dial_change(*args):
                try:
                    if numerical_step < step_coarse:
                        curr_dial = dial_widget.variable.get()
                        if hasattr(dial_widget, '_prev_dial_val_for_wrap_detection'):
                            if dial_widget._prev_dial_val_for_wrap_detection == 999 and curr_dial == 0:
                                fader_widget.variable.set(fader_widget.variable.get() + step_coarse)
                            elif dial_widget._prev_dial_val_for_wrap_detection == 0 and curr_dial == 999:
                                fader_widget.variable.set(fader_widget.variable.get() - step_coarse)
                        dial_widget._prev_dial_val_for_wrap_detection = curr_dial
                        base = math.floor(main_value_var.get() / step_coarse) * step_coarse
                        eff_range = step_coarse - numerical_step if (step_coarse - numerical_step) > 0 else step_coarse
                        new_fine = round(((curr_dial / 999.0) * eff_range) / numerical_step) * numerical_step
                        main_value_var.set(max(min_val, min(max_val, round((base + new_fine) / numerical_step) * numerical_step)))
                except: pass

            fader_widget.variable.trace_add("write", on_fader_change)
            dial_widget.variable.trace_add("write", on_dial_change)
            main_value_var.trace_add("write", update_widgets_from_main_var)
            
            def on_manual(e):
                try: 
                    val = round(float(entry_string_var.get()) / numerical_step) * numerical_step
                    main_value_var.set(max(min_val, min(max_val, val)))
                except: 
                    entry_string_var.set(format_string.format(main_value_var.get()))
            entry.bind("<FocusOut>", on_manual); entry.bind("<Return>", on_manual)

            def sync_bg():
                sync_entry_style()
                draw_f_label()
                draw_unit_label()
                if hasattr(fader_widget, "render"): fader_widget.render()
                if hasattr(dial_widget, "render"): dial_widget.render()
            
            sub_frame.render = sync_bg; sub_frame._draw = sync_bg

            update_widgets_from_main_var()
            if path:
                topic = state_mirror_engine.register_widget(path, main_value_var, base_mqtt_topic_from_path, config_data)
                def on_gui_change():
                    state_mirror_engine.broadcast_gui_change_to_mqtt(path)
                bind_variable_trace(main_value_var, on_gui_change)
                if subscriber_router and topic:
                    subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
                state_mirror_engine.initialize_widget_state(path)

            return sub_frame
        except Exception as e:
            if BUILDER_DEBUG: logger.exception(f"❌🚫🛑 [ERROR] Critical failure creating composite '{label}'")
            return None

    # Mixin bridge
    def make_knob(self, parent_widget, config_data, context=None, **kwargs):
        b_inst = kwargs.pop('builder_instance', self)
        return BuilderKnobCreator.make(parent_widget, config_data, context, builder_instance=b_inst, **kwargs)
