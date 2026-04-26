# input_inc_dec_buttons/input_inc_dec_buttons.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: input_inc_dec_buttons/dynamic_guimake_input_inc_dec_buttons.py

import inspect
import tkinter as tk
from tkinter import ttk

from oaConfigurationManager.FileReaders.config_reader import Config

# --- Standard Debug Logging Setup ---
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()

from oaGui.Methods.i18n_utils import get_text
from oaGui.Core.transparency.transparency_mixin import TransparencyMixin


class BuilderInputIncDecButtonsCreator(TransparencyMixin):
    # Creates a set of increment and decrement buttons along with a display for their current value.
    # This method sets up two buttons (up/down arrows) that, when pressed, modify a numerical
    # value. The current value is displayed, and the entire widget is synchronized via MQTT.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): Configuration for the increment/decrement buttons.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     tk.Frame: The created frame containing the increment/decrement buttons and value display.

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        creator = BuilderInputIncDecButtonsCreator()
        return creator.make_input_inc_dec_buttons(parent_widget, config_data, context, **kwargs)

    def make_input_inc_dec_buttons(
        self, parent_widget, config_data, context=None, **kwargs
    ):  # Updated signature
            """Creates increment/decrement buttons."""
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🔬🏗️🕹️ [BUILDER] Entering make_input_inc_dec_buttons", level="TRACE")
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📜📑💻 [CONFIG] Raw config received: {config_data}", level="DEBUG")

            current_function_name = "make_input_inc_dec_buttons"

            # Extract only widget-specific config from config_data
            label = get_text(config_data.get('label_active'))
            config = config_data  # config_data is the config
            path = config_data.get("path")

            # ⚡ HARDENED INTERFACE: Extract from context if available
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🔗🗂️⚙️ [CONTEXT] Extracting engine and router context...", level="TRACE")
            if context:
                state_mirror_engine = context.state_mirror_engine
                subscriber_router = context.subscriber_router
                base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
                builder_instance = context.builder_instance
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "✅🆗💻 [CONTEXT] Successfully extracted from WidgetContext object.", level="DEBUG")
            else:
                state_mirror_engine = self.state_mirror_engine
                subscriber_router = self.subscriber_router
                base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
                builder_instance = kwargs.get("builder_instance") or self
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "⚠️🔔🖱️ [CONTEXT] Context missing; fell back to self/kwargs.", level="DEBUG")

            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬⚡️🕹️ [BUILDER] Forging inc/dec buttons for '{label}' at path '{path}'.", level="DEBUG")

            frame = tk.Frame(parent_widget)  # Use parent_widget here

            # Apply Industrial Transparency
            if hasattr(self, '_apply_transparency'):
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "👻🌀🪟 [ALPHA] Applying industrial transparency to inc/dec frame.", level="TRACE")
                self._apply_transparency(frame, None, config_data, builder_instance)

            if label:
                tk.Label(frame, text=label, fg="white").pack(side=tk.LEFT, padx=(0, 10))

            # Initial value and range (optional, can be used for boundary checks)
            value_default = config.get("value_default", 0)
            increment_amount = config.get("increment", 1)
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📐📏✨ [STATE] Default value: {value_default}, Step: {increment_amount}", level="DEBUG")

            current_value = tk.IntVar(value=value_default)

            value_display = tk.Label(frame, textvariable=current_value, fg="white")
            value_display.pack(side=tk.RIGHT, padx=(10, 0))

            def sync_bg():
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🔄👻🎨 [SYNC] Syncing labels to background for inc/dec frame.", level="TRACE")
                bg = frame.cget("bg")
                for child in frame.winfo_children():
                    if isinstance(child, tk.Label):
                        child.config(bg=bg)

            frame._draw = sync_bg

            def _increment():
                new_val = current_value.get() + increment_amount
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🖱️👆🆙 [INPUT] Increment clicked for '{label}'. New: {new_val}", level="INFO")
                current_value.set(new_val)

            def _decrement():
                new_val = current_value.get() - increment_amount
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🖱️👆⬇️ [INPUT] Decrement clicked for '{label}'. New: {new_val}", level="INFO")
                current_value.set(new_val)

            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🏗️🔳🕹️ [CONSTRUCT] Instantiating inc/dec ttk.Buttons.", level="TRACE")
            dec_button = ttk.Button(frame, text="⬇", command=_decrement)
            dec_button.pack(side=tk.RIGHT)

            inc_button = ttk.Button(frame, text="⬆", command=_increment)
            inc_button.pack(side=tk.RIGHT, padx=(5, 0))

            # --- New MQTT Wiring for Inc/Dec Buttons ---
            if path:  # state_mirror_engine and subscriber_router are now explicitly passed
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📡📶🔗 [MQTT] Registering inc/dec buttons at path '{path}'", level="TRACE")
                widget_id = path

                # 1. Register widget
                topic = state_mirror_engine.register_widget(
                    widget_id, current_value, base_mqtt_topic_from_path, config
                )

                # 2. Subscribe to this widget's topic to receive updates
                if subscriber_router and topic:
                    matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📥📶🔄 [MQTT] Subscribing to topic: {topic}", level="DEBUG")
                    subscriber_router.subscribe_to_topic(
                        topic, state_mirror_engine.sync_incoming_mqtt_to_gui
                    )

                # 3. Bind variable trace for outgoing messages
                # Use a lambda that calls broadcast_gui_change_to_mqtt
                def on_gui_change(*args):
                    matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"⚡🔴📡 [EVENT] Value change for inc/dec '{label}'. Broadcasting.", level="DEBUG")
                    state_mirror_engine.broadcast_gui_change_to_mqtt(widget_id)

                current_value.trace_add("write", on_gui_change)

                # 4. Initialize state from cache or broadcast
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🔄⏳🔋 [STATE] Initializing state from cache/broker.", level="TRACE")
                state_mirror_engine.initialize_widget_state(widget_id)

            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"✅🆗🕹️ [SUCCESS] The increment/decrement buttons for '{label}' has materialized!", level="SUCCESS")
            return frame

