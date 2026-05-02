# button_toggler/button_toggler.py
# Author: Anthony Peter Kuzub
# Version: 20260323.Homoginized.1
#
# Description: Homoginized photorealistic Button Toggler (Radio Group) based on Actuator design.

import tkinter as tk

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from oaGui.Methods.formatting.i18n_utils import get_text
from oaGui.Core.factory.base_widget_creator import BaseWidgetCreator
from oaGui.Core.factory.button_canvas_base import CanvasButton
from oaGui.Hooks.registry.registry_widget_store import RegistryWidgetStore
from oaGui.Workers.compositing.sync_behavior import SyncBehavior


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

        value, units = self.option_data.get("value"), self.option_data.get("units")
        if value is not None or units is not None:
            suffix = f"\n({value if value else ''}{units if units else ''})"
            # ⚡ I18N SUPPORT: Apply suffix to each language in the dict, or the flat string
            if isinstance(self.on_text, dict):
                self.on_text = {lang: str(txt) + suffix for lang, txt in self.on_text.items()}
            else:
                self.on_text = str(self.on_text) + suffix

            if isinstance(self.off_text, dict):
                self.off_text = {lang: str(txt) + suffix for lang, txt in self.off_text.items()}
            else:
                self.off_text = str(self.off_text) + suffix

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

@RegistryWidgetStore.register("_GuiButtonToggler", "_SmartToggleGroup", "_ButtonToggler")
class BuilderButtonTogglerCreator(BaseWidgetCreator, SyncBehavior):
    """Factory for creating Button Toggler groups."""

    is_composite = True

    def _assemble_ui(self, parent_widget, config_data, context, **kwargs):
        """
        Implementation of the Template Method for Toggler group assembly.
        """
        ctx = context if context else type('obj', (object,), kwargs)()
        b_inst = getattr(ctx, 'builder_instance', None) or getattr(ctx, 'app_instance', None) or kwargs.get('builder_instance')

        path = config_data.get("path")
        label = get_text(config_data.get('label'), "")

        # 1. Main Canvas Container
        group_canvas = tk.Canvas(parent_widget, bd=0, highlightthickness=0, relief="flat")

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
        group_canvas.variable = selected_keys_var

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

            col_num += 1
            if col_num >= max_cols:
                col_num, row_num = 0, row_num + 1

        def sync_bg():
            redraw_labels()
            for btn in buttons.values():
                if hasattr(btn, "_draw"): btn._draw()
        group_canvas._draw = sync_bg
        group_canvas.render = sync_bg

        redraw_labels()
        return group_canvas, group_canvas

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        return BuilderButtonTogglerCreator.build(parent_widget, config_data, context, **kwargs)

    def make_button_toggler(self, parent_widget, config_data, context=None, **kwargs):
        """Legacy compatibility wrapper."""
        return self.build(parent_widget, config_data, context, **kwargs)
