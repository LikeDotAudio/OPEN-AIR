# checkbox/checkbox.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: checkbox/dynamic_guimake_checkbox.py

import inspect
import os
import tkinter as tk

# --- Standard Debug Logging Setup ---
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()

from oaGui.Methods.i18n_utils import get_text
from oaGui.Core.base_widget_creator import BaseWidgetCreator
from oaGui.Core.factory.widget_registry import WidgetRegistry
from oaGui.Core.transparency.transparency_mixin import TransparencyMixin

# --- Global Scope Variables ---
current_file = f"{os.path.basename(__file__)}"

# --- Constants ---
DEFAULT_PAD_X = 5
DEFAULT_PAD_Y = 2

@WidgetRegistry.register("_Checkbox", "_SmartCheckbox", "_GuiCheckbox")
class BuilderCheckboxCreator(BaseWidgetCreator, TransparencyMixin):
    """
    Factory for creating photorealistic Checkboxes.
    """

    def _assemble_ui(self, parent_widget, config_data, context, **kwargs):
        """Assembles the Checkbox UI elements."""
        current_function_name = inspect.currentframe().f_code.co_name
        config = config_data
        label = get_text(config.get('label_active')) or get_text(config.get('label'), "")

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬 Entering _assemble_ui for '{label}'.", level="DEBUG")

        try:
            # Use tk.Canvas for transparency support
            canvas = tk.Canvas(
                parent_widget,
                bd=0,
                highlightthickness=0,
                relief="flat",
                height=30,
                width=150
            )

            # We use a BooleanVar to track the state of the checkbox.
            initial_value = bool(config.get("value", False))
            state_var = kwargs.get("variable") or tk.BooleanVar(master=parent_widget, value=initial_value)
            canvas.variable = state_var

            def get_label_text():
                current_state = state_var.get()
                if current_state:
                    return get_text(config.get("label_active"), get_text(config.get("label"), ""))
                else:
                    return get_text(config.get("label_inactive"), get_text(config.get("label"), ""))

            def redraw_checkbox(*args):
                if not canvas.winfo_exists(): return
                canvas.delete("vu_element")
                canvas.delete("industrial_text")
                w = canvas.winfo_width()
                h = canvas.winfo_height()
                if w <= 1: return

                current_state = state_var.get()
                box_size = 16
                bx, by = 10, h/2 - box_size/2

                # Draw Box
                canvas.create_rectangle(
                    bx, by, bx + box_size, by + box_size,
                    outline="white", width=1, tags="vu_element"
                )

                if current_state:
                    # Draw Checkmark
                    canvas.create_line(
                        bx+3, by+box_size/2, bx+box_size/2, by+box_size-3,
                        fill="#00ff00", width=2, tags="vu_element"
                    )
                    canvas.create_line(
                        bx+box_size/2, by+box_size-3, bx+box_size-3, by+3,
                        fill="#00ff00", width=2, tags="vu_element"
                    )

                # Draw Label
                canvas.create_text(
                    bx + box_size + 10, h/2, text=get_label_text(),
                    fill="white", font=("Helvetica", 9), anchor="w",
                    tags="industrial_text"
                )

            def toggle_state(event):
                state_var.set(not state_var.get())
                redraw_checkbox()

            canvas.bind("<Button-1>", toggle_state)
            canvas.bind("<Configure>", redraw_checkbox, add="+")
            state_var.trace_add("write", lambda *a: redraw_checkbox())

            redraw_checkbox()
            return canvas, canvas

        except Exception as e:
            logger.exception(f"❌ Error in _assemble_ui for '{label}': {e}")
            return None, None

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        return BuilderCheckboxCreator.build(parent_widget, config_data, context, **kwargs)

    def make_checkbox(self, parent_widget, config_data, context=None, **kwargs):
        return self.build(parent_widget, config_data, context, **kwargs)
