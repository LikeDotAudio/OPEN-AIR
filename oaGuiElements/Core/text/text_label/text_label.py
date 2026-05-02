# text_label/text_label.py
import inspect

# Author: Anthony Peter Kuzub
# Version: 20260221.Standardized.1
#
# Description: A mixin class for the LoaderOrchestrator that handles the creation of a label widget.
import tkinter as tk

# --- Standard Debug Logging Setup ---
from oaConfigurationManager.FileReaders.config_reader import Config
from oaGui.Methods.formatting.i18n_utils import get_text
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()

from oaGui.Core.factory.base_widget_creator import BaseWidgetCreator
from oaGui.Hooks.registry.registry_widget_store import RegistryWidgetStore
from oaGui.Workers.compositing.sync_behavior import SyncBehavior


@RegistryWidgetStore.register("_Label", "_SmartLabel", "_GuiLabel")
class BuilderTextLabelCreator(BaseWidgetCreator, SyncBehavior):
    """
    Factory for creating photorealistic Text Labels.
    """

    def _assemble_ui(self, parent_widget, config_data, context, **kwargs):
        """Assembles the Text Label UI elements."""
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬 Entering _assemble_ui with config: {config_data}", level="TRACE")

        config = config_data
        label = get_text(config.get("label_active"), get_text(config.get("label"), "Label"))
        value = config.get("value", "")
        units = config.get("units", config.get("unit_text", ""))

        # Robust Background Inheritance
        try:
            p_bg = parent_widget.cget("bg")
            if not p_bg or not p_bg.startswith("#"): p_bg = "#2b2b2b"
        except:
            p_bg = "#2b2b2b"

        # Use tk.Canvas for sub_frame to support background slicing
        sub_frame = tk.Canvas(
            parent_widget,
            bd=0,
            highlightthickness=0,
            relief="flat",
            height=25, # Default height for label
            bg=p_bg
        )

        layout_config = config.get("layout", {})
        font_size = layout_config.get("font", 10)
        custom_font = ("Helvetica", font_size)
        custom_colour = layout_config.get("colour", None)

        label_text = f"{label}: {value}" if value else label
        if units:
            label_text += f" {units}"

        label_var = kwargs.get("variable") or tk.StringVar(master=parent_widget, value=label_text)
        sub_frame.variable = label_var

        def redraw_canvas_text(*args):
            if not sub_frame.winfo_exists(): return
            sub_frame.delete("industrial_text")
            w = sub_frame.winfo_width()
            h = sub_frame.winfo_height()
            if w <= 1: return

            txt = label_var.get()
            sub_frame.create_text(
                5, h/2, text=txt, anchor="w",
                fill=custom_colour or "white", font=custom_font,
                tags="industrial_text"
            )

        # Sync background hook
        def sync_bg():
            redraw_canvas_text()

        sub_frame._draw = sync_bg
        sub_frame.render = sync_bg

        label_var.trace_add("write", redraw_canvas_text)
        sub_frame.bind("<Configure>", redraw_canvas_text, add="+")

        return sub_frame, sub_frame

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        return BuilderTextLabelCreator.build(parent_widget, config_data, context, **kwargs)

    def make_text_label(self, parent_widget, config_data, context=None, **kwargs):
        return self.build(parent_widget, config_data, context, **kwargs)
