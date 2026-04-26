# fader_input/fader_input.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: A simple entry field that syncs with a DoubleVar (used by faders/knobs for numerical display).

import inspect
import tkinter as tk

from oaConfigurationManager.FileReaders.config_reader import Config

# --- Standard Debug Logging Setup ---
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()

from oaGui.Methods.i18n_utils import get_text
from oaGui.Core.transparency.transparency_mixin import TransparencyMixin
from oaOchestration.Methods.widget_event_binder import bind_variable_trace


class BuilderFaderInputCreator(TransparencyMixin):
    """Mixin for creating a simple entry field synced with a DoubleVar."""

    def make_fader_input(self, parent_widget, config_data, context=None, **kwargs):
        """Creates a simple text entry widget synced with a DoubleVar."""
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🔬🏗️📝 [BUILDER] Entering make_fader_input", level="TRACE")
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📜📑💻 [CONFIG] Raw config received: {config_data}", level="DEBUG")

        label = get_text(config_data.get('label_active'))
        path = config_data.get("path")
        variable = kwargs.get("variable")

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

        if not variable:
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🔋🔢✨ [STATE] No variable provided, creating new DoubleVar.", level="TRACE")
            variable = tk.DoubleVar()

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬⚡️📝 [BUILDER] Spawning fader input field for '{label}' at path '{path}'.", level="DEBUG")

        frame = tk.Frame(parent_widget)

        if hasattr(self, '_apply_transparency'):
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"👻🌀🪟 [ALPHA] Applying industrial transparency to input frame '{label}'", level="TRACE")
            self._apply_transparency(frame, None, config_data, builder_instance)

        if label:
            tk.Label(frame, text=label, fg="#dcdcdc", font=("Helvetica", 10)).pack(side=tk.TOP)

        entry = tk.Entry(frame, textvariable=variable, width=10, justify="center", bg="#1a1a1a", fg="#ffffff", insertbackground="white", bd=0, highlightthickness=1, highlightbackground="#444444")
        entry.pack(side=tk.TOP, pady=5)

        if path:
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📡📶🔗 [MQTT] Registering fader input at path '{path}'", level="TRACE")
            topic = state_mirror_engine.register_widget(path, variable, base_mqtt_topic_from_path, config_data)

            def on_gui_change():
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"⚡🔴📡 [EVENT] Input change for '{label}'. Broadcasting to MQTT.", level="DEBUG")
                state_mirror_engine.broadcast_gui_change_to_mqtt(path)

            bind_variable_trace(variable, on_gui_change)

            if subscriber_router and topic:
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📥📶🔄 [MQTT] Subscribing to topic: {topic}", level="DEBUG")
                subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)

            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔄⏳🔋 [STATE] Initializing state from cache/broker for '{path}'", level="TRACE")
            state_mirror_engine.initialize_widget_state(path)

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"✅🆗📝 [SUCCESS] The fader input '{label}' has materialized!", level="SUCCESS")
        return frame
