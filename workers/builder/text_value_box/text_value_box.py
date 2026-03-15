# text_value_box/dynamic_guimake_text_value_box.py
#
# This file provides the BuilderTextValueBoxCreator class for creating editable text box widgets in the GUI.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260110.2220.2

import os
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import inspect

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

from workers.handlers.widget_event_binder import bind_variable_trace
from workers.Command_Router.mqtt.mqtt_topic_utils import get_topic
from managers.Display.transparency.transparency_mixin import TransparencyMixin

# --- Global Scope Variables ---
current_file = f"{os.path.basename(__file__)}"

# --- Constants ---
DEFAULT_PAD_X = 5
DEFAULT_PAD_Y = 2


class BuilderTextValueBoxCreator(TransparencyMixin):
    """
    A mixin class that provides the functionality for creating an
    editable text box widget.
    """

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
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️📝 [BUILDER] Entering make_text_value_box")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config_data}")

        current_function_name = inspect.currentframe().f_code.co_name

        # Extract config
        label = config_data.get("label_active") or config_data.get("label", "")
        config = config_data
        path = config_data.get("path")
        units = config_data.get("units") or config_data.get("unit", "")

        # ⚡ HARDENED INTERFACE: Extract from context if available
        if BUILDER_DEBUG: builder_logger.trace("🔗🗂️⚙️ [CONTEXT] Extracting engine and router context...")
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            builder_instance = context.builder_instance
            if BUILDER_DEBUG: builder_logger.debug("✅🆗💻 [CONTEXT] Successfully extracted from WidgetContext object.")
        else:
            state_mirror_engine = self.state_mirror_engine
            subscriber_router = self.subscriber_router
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance") or self
            if BUILDER_DEBUG: builder_logger.debug("⚠️🔔🖱️ [CONTEXT] Context missing; fell back to self/kwargs.")

        if BUILDER_DEBUG: builder_logger.debug(f"🔬⚡️📝 [BUILDER] Forging value box for '{label}' at path '{path}'.")

        try:
            # Robust Background Inheritance
            try:
                p_bg = parent_widget.cget("bg")
                if not p_bg or not p_bg.startswith("#"): p_bg = "#2b2b2b"
            except:
                p_bg = "#2b2b2b"

            # Create the container frame - Use Canvas for alpha support
            if BUILDER_DEBUG: builder_logger.trace(f"🏗️🪟🎨 [CONSTRUCT] Creating canvas frame for value box '{label}'")
            sub_frame = tk.Canvas(
                parent_widget,
                bd=0,
                highlightthickness=0,
                relief="flat",
                height=25,
                bg=p_bg
            )
            
            # --- Layout Analysis ---
            if BUILDER_DEBUG: builder_logger.trace("📐📏🔳 [LAYOUT] Analyzing dimensions and grid configuration...")
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
                if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to value box.")
                self._apply_transparency(sub_frame, sub_frame, config, builder_instance)

            if BUILDER_DEBUG: builder_logger.debug(f"🧐📐🎨 [LAYOUT] Analysis for '{label}': H={box_height}, W={box_width}, Font={font_size}, Colour={custom_colour}")

            # --- Frame Sizing Logic ---
            if box_width is not None or box_height is not None:
                sub_frame.grid_propagate(False) # Stop resizing to content
                
                if box_height is not None:
                    sub_frame.config(height=box_height)
                
                if box_width is not None:
                    sub_frame.config(width=box_width)

            # 2. Entry Variable
            initial_value = config.get("value", "0")
            entry_value = tk.StringVar(value=initial_value)
            if BUILDER_DEBUG: builder_logger.debug(f"🔋📝✨ [STATE] Initial value for '{label}': '{initial_value}'")

            # 3. Entry Widget (Center)
            entry_font = ("TkDefaultFont", font_size)
            
            clean_path = path.replace('/', '_') if path else "default"
            style_name = f"DarkGrey.{clean_path}.TEntry"
            style = ttk.Style()
            
            text_color = "white"
            if custom_colour:
                text_color = custom_colour
                
            if BUILDER_DEBUG: builder_logger.trace(f"🎨🖌️✨ [STYLE] Configuring entry style '{style_name}'")
            style.configure(style_name, fieldbackground=sub_frame.cget("bg"), foreground=text_color, insertcolor="white")

            if BUILDER_DEBUG: builder_logger.trace(f"🏗️📝🔢 [CONSTRUCT] Instantiating ttk.Entry.")
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
                
                if BUILDER_DEBUG: builder_logger.trace(f"🔄🎨🔤 [REDRAW] Updating value box labels for '{label}'")
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
                if BUILDER_DEBUG: builder_logger.trace(f"🔄👻🎨 [SYNC] Syncing entry field background to: {bg}")
                # ⚡ HIGH-FIDELITY: Update the style's fieldbackground to match the sampled patina
                style.configure(style_name, fieldbackground=bg)
                redraw_box_labels()

            sub_frame._draw = sync_bg
            sub_frame.render = sync_bg
            sub_frame.bind("<Configure>", lambda e: redraw_box_labels(), add="+")

            # --- Event Binding ---
            def on_return(event):
                val = entry_value.get()
                if BUILDER_DEBUG: builder_logger.info(f"⌨️🔢🆗 [INPUT] Manual entry for value box '{label}': '{val}'")
                if state_mirror_engine:
                    if BUILDER_DEBUG: builder_logger.trace(f"📡🔴📡 [MQTT] Broadcasting manual entry for '{path}'")
                    state_mirror_engine.broadcast_gui_change_to_mqtt(path)

            if BUILDER_DEBUG: builder_logger.trace("⌨️👆🔗 [EVENTS] Binding return protocol to entry widget.")
            entry_widget.bind("<Return>", on_return)
            
            # --- MQTT Wiring ---
            if path and state_mirror_engine:
                if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [MQTT] Registering value box at path '{path}'")
                widget_id = path
                topic = state_mirror_engine.register_widget(
                    widget_id, entry_value, base_mqtt_topic_from_path, config
                )
                
                def on_gui_change():
                    if BUILDER_DEBUG: builder_logger.debug(f"⚡🔴📡 [EVENT] GUI change for value box '{label}'. Broadcasting.")
                    state_mirror_engine.broadcast_gui_change_to_mqtt(widget_id)
                
                bind_variable_trace(entry_value, on_gui_change)

                if subscriber_router and topic:
                    if BUILDER_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing to topic: {topic}")
                    subscriber_router.subscribe_to_topic(
                        topic, state_mirror_engine.sync_incoming_mqtt_to_gui
                    )
                
                if BUILDER_DEBUG: builder_logger.trace(f"🔄⏳🔋 [STATE] Initializing state from cache/broker for '{path}'")
                state_mirror_engine.initialize_widget_state(widget_id)

            if BUILDER_DEBUG: builder_logger.success(f"✅🆗📝 [SUCCESS] The text value box '{label}' has materialized!")
            return sub_frame

        except Exception as e:
            if BUILDER_DEBUG:
                builder_logger.exception(f"❌🚫🛑 [ERROR] Critical failure creating value box '{label}'")
            return None
