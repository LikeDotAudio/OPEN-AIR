# input_directional_buttons/input_directional_buttons.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: input_directional_buttons/dynamic_guimake_input_directional_buttons.py

import inspect
import time
import tkinter as tk
from tkinter import ttk

import orjson

from oaConfigurationManager.FileReaders.config_reader import Config

# --- Standard Debug Logging Setup ---
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()

from oaComProtocols.oaComMQTT.Methods.mqtt_topic_utils import get_topic
from oaGui.Methods.i18n_utils import get_text
from oaGui.Core.transparency.transparency_mixin import TransparencyMixin


class BuilderInputDirectionalButtonsCreator(TransparencyMixin):
    # Creates a set of directional buttons (up, down, left, right) and binds them to MQTT commands.
    # This method arranges four buttons in a cross pattern and configures each button
    # to publish a specific MQTT command when pressed, allowing for remote control of movement.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): Configuration for the directional buttons.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     tk.Frame: The created frame containing the directional buttons.

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        creator = BuilderInputDirectionalButtonsCreator()
        return creator.make_input_directional_buttons(parent_widget, config_data, context, **kwargs)

    def make_input_directional_buttons(
        self, parent_widget, config_data, context=None, **kwargs
    ):  # Updated signature
            """Creates a set of directional buttons (up, down, left, right)."""
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🔬🏗️🕹️ [BUILDER] Entering make_input_directional_buttons", level="TRACE")
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📜📑💻 [CONFIG] Raw config received: {config_data}", level="DEBUG")

            current_function_name = "make_input_directional_buttons"

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

            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬⚡️🕹️ [BUILDER] Spawning directional buttons for '{label}' at path '{path}'.", level="DEBUG")

            frame = tk.Frame(parent_widget)  # Use parent_widget here

            # Apply Industrial Transparency
            if hasattr(self, '_apply_transparency'):
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "👻🌀🪟 [ALPHA] Applying industrial transparency to directional frame.", level="TRACE")
                self._apply_transparency(frame, None, config_data, builder_instance)

            if label:
                tk.Label(frame, text=label, fg="white").grid(row=0, column=1, pady=(0, 5))

            def sync_bg():
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🔄👻🎨 [SYNC] Syncing labels to background for directional frame.", level="TRACE")
                bg = frame.cget("bg")
                for child in frame.winfo_children():
                    if isinstance(child, tk.Label):
                        child.config(bg=bg)

            frame._draw = sync_bg

            # Create buttons
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🏗️🔳🕹️ [CONSTRUCT] Instantiating directional ttk.Buttons.", level="TRACE")
            up_button = ttk.Button(frame, text="⬆")
            down_button = ttk.Button(frame, text="⬇")
            left_button = ttk.Button(frame, text="⬅")
            right_button = ttk.Button(frame, text="➡")

            up_button.grid(row=1, column=1)
            left_button.grid(row=2, column=0)
            right_button.grid(row=2, column=2)
            down_button.grid(row=3, column=1)

            # Commands (these would typically publish MQTT messages)
            def _publish_command(action):
                action_path = f"{path}/{action}"
                topic = get_topic(
                    self.state_mirror_engine.base_topic, base_mqtt_topic_from_path, action_path
                )
                payload_data = {
                    "value": True,
                    "src": "gui",
                    "timestamp": time.time(),
                    "GUID": self.state_mirror_engine.GUID,
                }
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📡🔴📡 [MQTT] Publishing directional command '{action}' to topic: {topic}", level="DEBUG")
                self.state_mirror_engine.publish_command(topic, orjson.dumps(payload_data).decode())

            def _move_up():
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🖱️👆⬆️ [INPUT] User clicked UP for '{path}'", level="INFO")
                _publish_command("up")

            def _move_down():
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🖱️👆⬇️ [INPUT] User clicked DOWN for '{path}'", level="INFO")
                _publish_command("down")

            def _move_left():
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🖱️👆⬅️ [INPUT] User clicked LEFT for '{path}'", level="INFO")
                _publish_command("left")

            def _move_right():
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🖱️👆➡ [INPUT] User clicked RIGHT for '{path}'", level="INFO")
                _publish_command("right")

            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🖱️👆🔗 [EVENTS] Binding command logic to directional buttons.", level="TRACE")
            up_button.config(command=_move_up)
            down_button.config(command=_move_down)
            left_button.config(command=_move_left)
            right_button.config(command=_move_right)

            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"✅🆗🕹️ [SUCCESS] The directional buttons for '{label}' has materialized!", level="SUCCESS")
            return frame

