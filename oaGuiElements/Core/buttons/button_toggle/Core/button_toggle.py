# button_toggle/button_toggle.py
# Author: Anthony Peter Kuzub
# Version: 20260323.Homoginized.1
#
# Description: Homoginized photorealistic Toggle Button based on Actuator design.

import tkinter as tk

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from oaGui.Methods.i18n_utils import get_text
from oaGui.Core.base_widget_creator import BaseWidgetCreator
from oaGui.Core.factory.button_canvas_base import CanvasButton
from oaGui.Core.factory.widget_registry import WidgetRegistry
from oaGui.Core.transparency.transparency_mixin import TransparencyMixin


class ToggleButton(CanvasButton):
    """
    A self-contained, stateful Toggle Button.
    Flips between two boolean states and maintains visual consistency.
    """
    def __init__(self, parent, config, builder_instance, variable=None, **kwargs):
        self.label = get_text(config.get("label"), "Toggle")
        self.config_data = config
        self.builder = builder_instance

        # Parse Options for Text
        options_map = config.get("options", {})
        self.on_text = get_text(config.get("label_active"), self.label if self.label else "ON")
        self.off_text = get_text(config.get("label_inactive"), self.label if self.label else "OFF")

        # State Variable
        is_on_init = options_map.get("ON", {}).get("selected", False)
        self.variable = variable or tk.BooleanVar(master=parent, value=is_on_init)

        # Super initialization (CanvasButton)
        super().__init__(
            parent, text=self.off_text, command=self._on_toggle,
            width=config.get("layout", {}).get("width", 100),
            height=config.get("layout", {}).get("height", 50),
            corner_radius=config.get("layout", {}).get("corner_radius", 6),
            bg_color=config.get("bg_color", "#1a1a1a"),
            active_color=config.get("active_color", "#FF9900"),
            active_bg_color=config.get("active_bg_color", "#000000"),
            text_color=config.get("text_color", "#888888"),
            active_text_color=config.get("active_text_color", "#1a1a1a"),
            glow_intensity=config.get("glow_intensity", 1.0),
            active_font_style=config.get("active_font_style", "bold"),
            active_font_size=config.get("active_font_size"),
            inactive_font_style=config.get("inactive_font_style", "normal"),
            inactive_font_size=config.get("inactive_font_size"),
            alpha=float(config.get("alpha", 1.0)),
            font=("TkDefaultFont", config.get("layout", {}).get("font", 10)),
            transparency_applicator=builder_instance._apply_transparency if hasattr(builder_instance, '_apply_transparency') else None,
            config=config, builder=builder_instance
        )

        # Sync with variable
        self.variable.trace_add("write", self._update_visual_state)
        self._update_visual_state()

    def _on_toggle(self, event=None):
        """Toggle the boolean state."""
        self.variable.set(not self.variable.get())

    def _update_visual_state(self, *args):
        """Syncs button appearance with the boolean variable."""
        is_on = self.variable.get()
        self.set_active(is_on)
        self.set_text(self.on_text if is_on else self.off_text)

@WidgetRegistry.register("_GuiButtonToggle", "_SmartToggle", "_ButtonToggle")
class BuilderButtonToggleCreator(BaseWidgetCreator, TransparencyMixin):
    """Factory for creating Toggle Buttons."""

    def _assemble_ui(self, parent_widget, config_data, context, **kwargs):
        """
        Implementation of the Template Method for Toggle Button assembly.
        """
        ctx = context if context else type('obj', (object,), kwargs)()
        b_inst = getattr(ctx, 'builder_instance', None) or getattr(ctx, 'app_instance', None) or kwargs.get('builder_instance')

        label = get_text(config_data.get('label'), "")

        if label:
            btn_w = max(1, int(config_data.get("layout", {}).get("width", 100)))
            btn_h = max(1, int(config_data.get("layout", {}).get("height", 50)))
            container = tk.Canvas(
                parent_widget, bd=0, highlightthickness=0, relief="flat",
                width=btn_w + 10, height=btn_h + 25
            )

            def redraw_labels():
                if not container.winfo_exists(): return
                container.delete("industrial_text")
                container.create_text(
                    (btn_w + 11)/2, 12, text=label, anchor="center",
                    fill="white", font=("TkDefaultFont", 10, "bold"),
                    tags="industrial_text"
                )

            container.bind("<Configure>", lambda e: redraw_labels(), add="+")
            redraw_labels()
            parent_for_button = container
        else:
            container = None
            parent_for_button = parent_widget

        button = ToggleButton(
            parent_for_button, config_data, b_inst,
            variable=kwargs.get("variable")
        )

        if container:
            button.place(x=5, y=25)
            def sync_bg():
                redraw_labels()
                if hasattr(button, "_draw"): button._draw()
            container._draw = sync_bg
            container.render = sync_bg
            container.variable = button.variable
            return container, container

        return button, button

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        return BuilderButtonToggleCreator.build(parent_widget, config_data, context, **kwargs)

    def make_button_toggle(self, parent_widget, config_data, context=None, **kwargs):
        """Legacy compatibility wrapper."""
        return self.build(parent_widget, config_data, context, **kwargs)
