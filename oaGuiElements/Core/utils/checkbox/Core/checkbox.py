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
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin

# --- Global Scope Variables ---
current_file = f"{os.path.basename(__file__)}"

# --- Constants ---
DEFAULT_PAD_X = 5
DEFAULT_PAD_Y = 2


class BuilderCheckboxCreator(TransparencyMixin):
    """
    A mixin class that provides the functionality for creating a
    checkbox widget.
    """

    # Creates a checkbox widget that manages a boolean state and synchronizes via MQTT.
    # This method sets up a Canvas-based checkbox to ensure true transparency.
    # It also integrates with the state management engine for MQTT communication.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): Configuration for the checkbox.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     tk.Canvas: The created canvas containing the checkbox, or None on failure.
    def make_checkbox(
        self, parent_widget, config_data, context=None, **kwargs
    ):
        """Creates a checkbox widget."""
        current_function_name = inspect.currentframe().f_code.co_name

        # Extract only widget-specific config from config_data
        label = get_text(get_text(config_data.get('label_active'))) or get_text(get_text(config_data.get('label')), "")
        config = config_data
        path = config_data.get("path")

        # ⚡ HARDENED INTERFACE: Extract from context if available
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            builder_instance = context.builder_instance
        else:
            state_mirror_engine = self.state_mirror_engine
            subscriber_router = self.subscriber_router
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance") or self

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬⚡️ Entering '{current_function_name}' to spawn a checkbox for '{label}'.", level="DEBUG")

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
            state_var = tk.BooleanVar(value=initial_value)

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

                if hasattr(canvas, 'panel_bg_image') and canvas.panel_bg_image:
                    canvas.delete("bg")
                    canvas.create_image(0, 0, image=canvas.panel_bg_image, anchor="nw", tags="bg")
                    canvas.tag_lower("bg")

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
                if path:
                    state_mirror_engine.broadcast_gui_change_to_mqtt(path)
                redraw_checkbox()

            # Apply Industrial Transparency
            if hasattr(self, '_apply_transparency'):
                self._apply_transparency(canvas, canvas, config, builder_instance)

            canvas.bind("<Button-1>", toggle_state)
            canvas.bind("<Configure>", redraw_checkbox, add="+")
            state_var.trace_add("write", lambda *a: redraw_checkbox())

            # Store the widget and its state variable for external updates.
            if path:
                widget_id = path
                topic = state_mirror_engine.register_widget(
                    widget_id, state_var, base_mqtt_topic_from_path, config
                )

                # Subscribe to this widget's topic to receive updates
                if subscriber_router and topic:
                    subscriber_router.subscribe_to_topic(
                        topic, state_mirror_engine.sync_incoming_mqtt_to_gui
                    )

                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬 Widget '{label}' ({path}) registered with StateMirrorEngine (BooleanVar: {state_var.get()}).", level="DEBUG")
                # Initialize state from cache or broadcast
                state_mirror_engine.initialize_widget_state(path)

            redraw_checkbox()

            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"✅ SUCCESS! The checkbox '{label}' has been successfully instantiated.", level="SUCCESS")
            return canvas

        except Exception:
            logger.exception("❌ Error in make_checkbox for '{label}'")
            return None

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        creator = BuilderCheckboxCreator()
        return creator.make_checkbox(parent_widget, config_data, context, **kwargs)
