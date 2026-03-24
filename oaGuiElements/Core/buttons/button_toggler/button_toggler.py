# button_toggler/button_toggler.py
# Author: Anthony Peter Kuzub
# Version: 20260323.Homoginized.1
#
# Description: Homoginized photorealistic Button Toggler (Radio Group) based on Actuator design.

import os
import tkinter as tk
from tkinter import ttk
import inspect
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config
app_constants = Config.get_instance()

from oaGuiManager.Core.factory.button_canvas_base import CanvasButton
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
from oaOchestration.Methods.widget_event_binder import bind_variable_trace
from oaComMQTT.Methods.mqtt_topic_utils import get_topic
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry

class TogglerButton(CanvasButton):
    """
    A self-contained button used within a Toggler (radio) group.
    """
    def __init__(self, parent, key, options_data, config, group_variable, on_click_callback, builder_instance, **kwargs):
        self.key = key
        self.group_variable = group_variable
        self.on_click_callback = on_click_callback
        self.option_data = options_data.get(key, {})
        self.label_base = self.option_data.get("label", key)
        
        # Derive text
        self.on_text = self.option_data.get("label_active", self.label_base)
        self.off_text = self.option_data.get("label_inactive", self.label_base)
        
        val, units = self.option_data.get("value"), self.option_data.get("units")
        if val is not None or units is not None:
            suffix = f"\n({val if val else ''}{units if units else ''})"
            self.on_text += suffix
            self.off_text += suffix

        # Layout configuration
        layout = config.get("layout", {})
        c_act = self.option_data.get("active_color", config.get("active_color", "#FF9900"))
        c_inact = self.option_data.get("bg_color", config.get("bg_color", "#1a1a1a"))

        super().__init__(
            parent, text=self.off_text, command=self._on_click,
            width=layout.get("width", 100), height=layout.get("height", 50),
            corner_radius=layout.get("corner_radius", 6),
            bg_color=c_inact, active_color=c_act,
            active_bg_color=config.get("active_bg_color", "#000000"),
            text_color=config.get("text_color", "#888888"),
            active_text_color=config.get("active_text_color", "#1a1a1a"),
            glow_intensity=config.get("glow_intensity", 1.0),
            active_font_style=config.get("active_font_style", "bold"),
            active_font_size=config.get("active_font_size"),
            inactive_font_style=config.get("inactive_font_style", "normal"),
            inactive_font_size=config.get("inactive_font_size"),
            alpha=float(config.get("alpha", 1.0)),
            font=("TkDefaultFont", layout.get("font", 10)),
            transparency_applicator=builder_instance._apply_transparency if hasattr(builder_instance, '_apply_transparency') else None,
            config=config, builder=builder_instance
        )

        self.group_variable.trace_add("write", self._update_visual_state)
        self._update_visual_state()

    def _on_click(self, event=None):
        self.on_click_callback(event, self.key)

    def _update_visual_state(self, *args):
        selected_keys = self.group_variable.get().split(",") if self.group_variable.get() else []
        is_sel = self.key in selected_keys
        self.set_active(is_sel)
        self.set_text(self.on_text if is_sel else self.off_text)

@WidgetRegistry.register("_GuiButtonToggler", "_SmartToggleGroup", "_ButtonToggler")
class BuilderButtonTogglerCreator(TransparencyMixin):
    """Factory for creating Button Toggler groups."""

    def make_button_toggler(self, parent_widget, config_data, context=None, **kwargs):
        ctx = context if context else type('obj', (object,), kwargs)()
        b_inst = ctx.builder_instance if hasattr(ctx, 'builder_instance') else ctx.app_instance
        
        path, b_topic = config_data.get("path"), ctx.base_mqtt_topic_from_path
        label = config_data.get("label", "")

        # 1. Main Canvas Container
        group_canvas = tk.Canvas(parent_widget, bd=0, highlightthickness=0, relief="flat")
        group_canvas._oca_path = path
        
        if hasattr(self, '_apply_transparency'):
            self._apply_transparency(group_canvas, group_canvas, config_data, b_inst)

        def redraw_labels():
            if not group_canvas.winfo_exists(): return
            group_canvas.delete("industrial_text")
            if label:
                group_canvas.create_text(
                    10, 12, text=label, anchor="w",
                    fill="white", font=("TkDefaultFont", 10, "bold"),
                    tags="industrial_text"
                )

        group_canvas.bind("<Configure>", lambda e: redraw_labels(), add="+")

        options_data = config_data.get("options", {})
        if isinstance(options_data, list):
            opt_dict = {}
            for item in options_data:
                opt_dict[str(item)] = {"label": str(item)}
            options_data = opt_dict

        initial_selected_key = next((k for k, opt in options_data.items() if str(opt.get("selected", "no")).lower() in ["yes", "true"]), "")
        selected_keys_var = kwargs.get("variable") or tk.StringVar(master=parent_widget, value=initial_selected_key)

        layout = config_data.get("layout", {})
        max_cols = int(layout.get("max_cols", 4))
        grid_padx = int(layout.get("padx", 5))
        grid_pady = int(layout.get("pady", 5))
        selection_mode = config_data.get("selection_mode", "one").lower()
        if selection_mode == "one": selection_mode = "radio"
        allow_null = config_data.get("Allow_Null", False)
        allow_multi_alt = config_data.get("Allow_Multi_Alt_Select", False)

        buttons = {}

        def on_button_click(event, key):
            current_selected_keys = selected_keys_var.get().split(",") if selected_keys_var.get() else []
            is_multi = (selection_mode == "multi") or (allow_multi_alt and event and (event.state & 0x0008))
            
            if is_multi:
                if key in current_selected_keys:
                    current_selected_keys.remove(key)
                else:
                    current_selected_keys.append(key)
            else:
                if key in current_selected_keys:
                    if allow_null: current_selected_keys = []
                    else: return
                else:
                    current_selected_keys = [key]
            
            selected_keys_var.set(",".join(current_selected_keys))

        row_num = 1 if label else 0
        col_num = 0
        if label: group_canvas.grid_rowconfigure(0, minsize=25)

        for idx, option_key in enumerate(options_data.keys()):
            button = TogglerButton(
                group_canvas, option_key, options_data, config_data, 
                selected_keys_var, on_button_click, b_inst
            )
            button.grid(row=row_num, column=col_num, padx=grid_padx, pady=grid_pady, sticky="nsew")
            group_canvas.grid_columnconfigure(col_num, weight=1)
            buttons[option_key] = button
            if idx == 0 and path: button._oca_path = path 
            
            col_num += 1
            if col_num >= max_cols:
                col_num, row_num = 0, row_num + 1

        if path and ctx.state_mirror_engine:
            topic = ctx.state_mirror_engine.register_widget(path, selected_keys_var, b_topic, config_data)
            bind_variable_trace(selected_keys_var, lambda: ctx.state_mirror_engine.broadcast_gui_change_to_mqtt(path))
            if ctx.subscriber_router and topic:
                ctx.subscriber_router.subscribe_to_topic(topic, ctx.state_mirror_engine.sync_incoming_mqtt_to_gui)
            ctx.state_mirror_engine.initialize_widget_state(path)

        def sync_bg():
            redraw_labels()
            for btn in buttons.values():
                if hasattr(btn, "_draw"): btn._draw()
        group_canvas._draw = sync_bg
        group_canvas.render = sync_bg

        redraw_labels()
        return group_canvas

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        creator = BuilderButtonTogglerCreator()
        return creator.make_button_toggler(parent_widget, config_data, context, **kwargs)
