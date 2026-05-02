# text_value_box/text_value_box.py
# Author: Anthony Peter Kuzub
# Version: 20260110.2220.2
#
# Description: text_value_box/dynamic_guimake_text_value_box.py

import inspect
import os
import tkinter as tk
from tkinter import ttk

from oaConfigurationManager.FileReaders.config_reader import Config

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import builder_logger
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()  # Get the singleton instance

from oaGui.Methods.formatting.i18n_utils import get_text
from oaGui.Workers.compositing.sync_behavior import SyncBehavior
from oaOchestration.Methods.widget_event_binder import bind_variable_trace

# --- Global Scope Variables ---
current_file = f"{os.path.basename(__file__)}"

# --- Constants ---
DEFAULT_PAD_X = 5
DEFAULT_PAD_Y = 2


class BuilderTextValueBoxCreator(SyncBehavior):
    """
    A mixin class that provides the functionality for creating an
    editable text box widget.
    """

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        creator = BuilderTextValueBoxCreator()
        return creator.make_text_value_box(parent_widget, config_data, context, **kwargs)

    # Creates an editable text box widget for displaying and modifying a single value.
    # This method sets up a Label (optional), an Entry box, and a Units label (optional).
    # It supports layout customization (width, height, font) and full MQTT synchronization.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): Configuration for the value box.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     tk.Frame: The created frame containing the value box, or None on failure.
    def make_text_value_box(
        self, parent_widget, config_data, context=None, **kwargs
    ):
        """Creates an editable text box widget."""
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🔬🏗️📝 [BUILDER] Entering make_text_value_box", level="TRACE")
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📜📑💻 [CONFIG] Raw config received: {config_data}", level="DEBUG")

        current_function_name = inspect.currentframe().f_code.co_name

        # Extract config
        label = get_text(get_text(config_data.get('label_active'))) or get_text(get_text(config_data.get('label')), "")
        config = config_data
        path = config_data.get("path")
        units = config_data.get("units") or config_data.get("unit", "")

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

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬⚡️📝 [BUILDER] Forging value box for '{label}' at path '{path}'.", level="DEBUG")

        try:
            # Robust Background Inheritance
            try:
                p_bg = parent_widget.cget("bg")
                if not p_bg or not p_bg.startswith("#"): p_bg = "#2b2b2b"
            except:
                p_bg = "#2b2b2b"

            # Create the container frame - Use Canvas for alpha support
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🏗️🪟🎨 [CONSTRUCT] Creating canvas frame for value box '{label}'", level="TRACE")
            sub_frame = tk.Canvas(
                parent_widget,
                bd=0,
                highlightthickness=0,
                relief="flat",
                height=25,
                bg=p_bg
            )

            # --- Layout Analysis ---
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "📐📏🔳 [LAYOUT] Analyzing dimensions and grid configuration...", level="TRACE")
            layout = config.get("layout", {})
            geometry = config.get("geometry", {})
            box_height = geometry.get("height", layout.get("height"))
            box_width = geometry.get("width", layout.get("width"))
            font_size = geometry.get("font", layout.get("font", 10))
            custom_colour = geometry.get("colour", layout.get("colour"))

            # Configure Grid: Label (0), Entry (1), Units (2)
            # CRITICAL: Entry column MUST have weight 1 to fill sub_frame
            # Reserve space for labels in columns 0 and 2
            sub_frame.grid_columnconfigure(0, minsize=60 if label else 0)
            sub_frame.grid_columnconfigure(1, weight=1)
            sub_frame.grid_columnconfigure(2, minsize=40 if units else 0)
            sub_frame.grid_rowconfigure(0, weight=1)

            # Apply Industrial Transparency
            if hasattr(self, '_apply_transparency'):
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "👻🌀🪟 [ALPHA] Applying industrial transparency to value box.", level="TRACE")
                self._apply_transparency(sub_frame, sub_frame, config, builder_instance)

            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🧐📐🎨 [LAYOUT] Analysis for '{label}': H={box_height}, W={box_width}, Font={font_size}, Colour={custom_colour}", level="DEBUG")

            # --- Frame Sizing Logic ---
            if box_width is not None or box_height is not None:
                sub_frame.grid_propagate(False) # Stop resizing to content

                if box_height is not None:
                    sub_frame.config(height=box_height)

                if box_width is not None:
                    sub_frame.config(width=box_width)

            # 2. Entry Variable
            initial_value = config.get("value", "0")
            entry_value = kwargs.get("variable") or tk.StringVar(master=parent_widget, value=initial_value)
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔋📝✨ [STATE] Initial value for '{label}': '{initial_value}'", level="DEBUG")

            # 3. Entry Widget (Center)
            entry_font = ("TkDefaultFont", font_size)

            clean_path = path.replace('/', '_') if path else "default"
            style_name = f"DarkGrey.{clean_path}.TEntry"
            style = ttk.Style()

            text_color = "white"
            if custom_colour:
                text_color = custom_colour

            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🎨🖌️✨ [STYLE] Configuring entry style '{style_name}'", level="TRACE")
            style.configure(style_name, fieldbackground=sub_frame.cget("bg"), foreground=text_color, insertcolor="white")

            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🏗️📝🔢 [CONSTRUCT] Instantiating ttk.Entry.", level="TRACE")
            entry_widget = ttk.Entry(
                sub_frame,
                textvariable=entry_value,
                font=entry_font,
                justify="center",
                style=style_name
            )

            # STICKY NSEW ensures it fills the calculated frame height/width!
            entry_widget.grid(row=0, column=1, sticky="nsew", padx=DEFAULT_PAD_X)

            sub_frame._last_redraw_size = (0, 0)

            def redraw_box_labels(*args):
                if not sub_frame.winfo_exists(): return

                w = sub_frame.winfo_width()
                h = sub_frame.winfo_height()

                # ⚡ OPTIMIZATION: Skip if size hasn't changed
                if (w, h) == sub_frame._last_redraw_size:
                    return

                if w <= 1 or h <= 1: return

                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔄🎨🔤 [REDRAW] Updating value box labels for '{label}'", level="TRACE")
                sub_frame._last_redraw_size = (w, h)
                sub_frame.delete("industrial_text")

                # Label (Left)
                if label and label != "X":
                    sub_frame.create_text(
                        5, h/2, text=f"{label}:", anchor="w",
                        fill=custom_colour or "white", font=("TkDefaultFont", font_size),
                        tags="industrial_text"
                    )

                # Units (Right)
                if units:
                    sub_frame.create_text(
                        w-5, h/2, text=units, anchor="e",
                        fill=custom_colour or "white", font=("TkDefaultFont", font_size),
                        tags="industrial_text"
                    )

            def sync_bg():
                if not sub_frame.winfo_exists(): return
                bg = sub_frame.cget("bg")
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔄👻🎨 [SYNC] Syncing entry field background to: {bg}", level="TRACE")
                # ⚡ HIGH-FIDELITY: Update the style's fieldbackground to match the sampled patina
                style.configure(style_name, fieldbackground=bg)
                redraw_box_labels()

            sub_frame._draw = sync_bg
            sub_frame.render = sync_bg
            sub_frame.bind("<Configure>", lambda e: redraw_box_labels(), add="+")

            # --- Event Binding ---
            def on_return(event):
                value = entry_value.get()
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"⌨️🔢🆗 [INPUT] Manual entry for value box '{label}': '{value}'", level="INFO")
                if state_mirror_engine:
                    matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📡🔴📡 [MQTT] Broadcasting manual entry for '{path}'", level="TRACE")
                    state_mirror_engine.broadcast_gui_change_to_mqtt(path)

            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "⌨️👆🔗 [EVENTS] Binding return protocol to entry widget.", level="TRACE")
            entry_widget.bind("<Return>", on_return)

            # --- MQTT Wiring ---
            if path and state_mirror_engine:
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📡📶🔗 [MQTT] Registering value box at path '{path}'", level="TRACE")
                widget_id = path
                topic = state_mirror_engine.register_widget(
                    widget_id, entry_value, base_mqtt_topic_from_path, config
                )

                def on_gui_change():
                    matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"⚡🔴📡 [EVENT] GUI change for value box '{label}'. Broadcasting.", level="DEBUG")
                    state_mirror_engine.broadcast_gui_change_to_mqtt(widget_id)

                bind_variable_trace(entry_value, on_gui_change)

                if subscriber_router and topic:
                    matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📥📶🔄 [MQTT] Subscribing to topic: {topic}", level="DEBUG")
                    subscriber_router.subscribe_to_topic(
                        topic, state_mirror_engine.sync_incoming_mqtt_to_gui
                    )

                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔄⏳🔋 [STATE] Initializing state from cache/broker for '{path}'", level="TRACE")
                state_mirror_engine.initialize_widget_state(widget_id)

            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"✅🆗📝 [SUCCESS] The text value box '{label}' has materialized!", level="SUCCESS")
            return sub_frame

        except Exception:
            builder_logger.exception(f"❌🚫🛑 [ERROR] Critical failure creating value box '{label}'")
            return None
