# button_toggler/button_toggler.py
#
# This file provides the BuilderButtonTogglerCreator class for creating groups of radio-style buttons in the GUI.
# Updated to support WYSIWYG resizing via the first button in the group.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20260220.Modular.1

import os
import tkinter as tk
from tkinter import ttk
import inspect
import math
from PIL import Image, ImageDraw, ImageTk, ImageFont, ImageFilter, ImageChops

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

from managers.Display.transparency.transparency_mixin import TransparencyMixin
from workers.handlers.widget_event_binder import bind_variable_trace
from workers.Command_Router.mqtt.mqtt_topic_utils import get_topic
from managers.Display.factory.button_canvas_base import CanvasButton

# --- Constants ---
DEFAULT_PAD_X = 5
DEFAULT_PAD_Y = 2

class BuilderButtonTogglerCreator(TransparencyMixin):
    """
    A mixin class that provides the functionality for creating a
    group of buttons that behave like radio buttons.
    """

    def make_button_toggler(
        self,
        parent_widget,
        config_data,
        context=None,
        **kwargs
    ):
        """Creates a set of custom buttons that behave like radio buttons."""
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️🔘 [BUILDER] Entering make_button_toggler")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config_data}")

        current_function_name = inspect.currentframe().f_code.co_name

        label = config_data.get("label_active") or config_data.get("label", "")
        config = config_data
        path = config_data.get("path")

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

        if BUILDER_DEBUG: builder_logger.debug(f"🔬⚡️🔘 [BUILDER] Spawning button toggler group for '{label}' at path '{path}'.")

        try:
            # 1. Main Canvas Container
            if BUILDER_DEBUG: builder_logger.trace(f"🏗️🪟🎨 [CONSTRUCT] Creating main canvas container for toggler '{label}'")
            group_canvas = tk.Canvas(
                parent_widget,
                bd=0,
                highlightthickness=0,
                relief="flat"
            )
            # EXPOSE CONTAINER TO WYSIWYG
            group_canvas._oca_path = path
            
            if hasattr(self, '_apply_transparency'):
                if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to toggler container '{label}'")
                self._apply_transparency(group_canvas, group_canvas, config, builder_instance)

            group_canvas._last_redraw_size = (0, 0)

            def redraw_labels(*args):
                if not group_canvas.winfo_exists(): return
                w = group_canvas.winfo_width()
                h = group_canvas.winfo_height()
                if (w, h) == group_canvas._last_redraw_size:
                    return
                if w <= 1: return
                group_canvas._last_redraw_size = (w, h)
                
                if BUILDER_DEBUG: builder_logger.trace(f"🔄🎨🔤 [REDRAW] Redrawing labels for toggler '{label}'")
                group_canvas.delete("industrial_text")
                if label:
                    group_canvas.create_text(
                        10, 12, text=label, anchor="w",
                        fill="white", font=("TkDefaultFont", 10, "bold"),
                        tags="industrial_text"
                    )

            def sync_bg():
                redraw_labels()
                for btn in buttons.values():
                    if hasattr(btn, "_draw"): btn._draw()
                
            group_canvas._draw = sync_bg
            group_canvas.render = sync_bg
            group_canvas.bind("<Configure>", lambda e: redraw_labels(), add="+")

            options_data = config.get("options", {})
            if isinstance(options_data, list):
                if BUILDER_DEBUG: builder_logger.debug(f"⚠️🔔🔡 [CONFIG] Options for '{label}' is a list, converting to dict.")
                opt_dict = {}
                for item in options_data:
                    opt_dict[str(item)] = {"label": str(item)}
                options_data = opt_dict

            buttons = {}
            initial_selected_key = next((k for k, opt in options_data.items() if str(opt.get("selected", "no")).lower() in ["yes", "true"]), "")
            selected_keys_var = tk.StringVar(value=initial_selected_key)
            if BUILDER_DEBUG: builder_logger.debug(f"🔋🔘✨ [STATE] Initial selected keys for '{label}': {initial_selected_key}")

            layout = config.get("layout", {})
            font_size = layout.get("font", 10)
            button_height = layout.get("height", 50)
            button_width = layout.get("width", 100)
            max_cols = int(layout.get("max_cols", 4))
            grid_padx = int(layout.get("padx", 5))
            grid_pady = int(layout.get("pady", 5))
            if BUILDER_DEBUG: builder_logger.debug(f"📐📏🔳 [LAYOUT] Grid: max_cols={max_cols}, pads=({grid_padx},{grid_pady}), btn_dim={button_width}x{button_height}")
            
            selection_mode = config.get("selection_mode", "one").lower()
            if selection_mode == "one": selection_mode = "radio"
            
            # --- New: Allow_Null and Allow_Multi_Alt_Select ---
            allow_null = config.get("Allow_Null", False)
            allow_multi_alt = config.get("Allow_Multi_Alt_Select", False)
            if BUILDER_DEBUG: builder_logger.debug(f"⚙️🔀✅ [CONFIG] Mode: {selection_mode}, AllowNull: {allow_null}, MultiAlt: {allow_multi_alt}")
            
            def update_button_styles(*args):
                selected_keys = selected_keys_var.get().split(",") if selected_keys_var.get() else []
                if BUILDER_DEBUG: builder_logger.trace(f"✨🔄🎨 [SYNC] Updating styles for '{label}' group. Selected: {selected_keys}")
                for key, button_widget in buttons.items():
                    option_data = options_data.get(key, {})
                    is_sel = key in selected_keys
                    button_text = option_data.get("label_active" if is_sel else "label_inactive", option_data.get("label", key))
                    
                    val, units = option_data.get("value"), option_data.get("units")
                    if val is not None or units is not None:
                        button_text += f"\n({val if val else ''}{units if units else ''})"

                    button_widget.set_active(is_sel)
                    button_widget.set_text(button_text)

            def on_button_click(event, key):
                if BUILDER_DEBUG: builder_logger.info(f"🖱️👆🔘 [INPUT] Toggler '{label}' button click: '{key}'")
                current_selected_keys = selected_keys_var.get().split(",") if selected_keys_var.get() else []
                
                # Check for multi-selection: either mode="multi" OR allow_multi_alt + Alt key
                is_multi = (selection_mode == "multi") or (allow_multi_alt and (event.state & 0x0008)) # 0x0008 is Alt
                if BUILDER_DEBUG and is_multi: builder_logger.trace(f"🔀🔳✨ [INPUT] Multi-selection mode active for click.")
                
                if is_multi:
                    if key in current_selected_keys:
                        current_selected_keys.remove(key)
                    else:
                        current_selected_keys.append(key)
                else:
                    # Single selection mode
                    if key in current_selected_keys:
                        # Clicking the already selected key
                        if allow_null:
                            if BUILDER_DEBUG: builder_logger.trace(f"❌🔲✨ [INPUT] Deselecting active key via Allow_Null.")
                            current_selected_keys = []
                        else:
                            # Do nothing, maintain selection
                            if BUILDER_DEBUG: builder_logger.trace(f"🆗🔳✨ [INPUT] Key already active, no change.")
                            return
                    else:
                        current_selected_keys = [key]
                
                new_keys_str = ",".join(current_selected_keys)
                if BUILDER_DEBUG: builder_logger.debug(f"⚡🔄🔋 [STATE] Toggler '{label}' new state: {new_keys_str}")
                selected_keys_var.set(new_keys_str)

            # Create Buttons
            glow_int = config.get("glow_intensity", 1.0)
            alpha = float(config.get("alpha", layout.get("alpha", 1.0)))
            corner_radius = layout.get("corner_radius", 6)

            row_num = 1 if label else 0
            col_num = 0
            
            if label:
                group_canvas.grid_rowconfigure(0, minsize=25)

            if BUILDER_DEBUG: builder_logger.trace(f"🏗️🔳🕹️ [CONSTRUCT] Iterating through options to create CanvasButtons for '{label}'")
            for idx, (option_key, option_data) in enumerate(options_data.items()):
                c_act = option_data.get("active_color", config.get("active_color", "#FF9900"))
                
                # ⚡ DETERMINISTIC: Default to a fixed dark grey for the inactive state
                c_inact = option_data.get("bg_color", config.get("bg_color", "#1a1a1a"))
                
                button = CanvasButton(
                    group_canvas, text="Init", command=lambda e, k=option_key: on_button_click(e, k),
                    width=button_width, height=button_height, corner_radius=corner_radius,
                    bg_color=c_inact, active_color=c_act,
                    glow_intensity=glow_int, alpha=alpha, font=("TkDefaultFont", font_size),
                    transparency_applicator=builder_instance._apply_transparency if hasattr(builder_instance, '_apply_transparency') else None,
                    config=config, builder=builder_instance
                )
                button.grid(row=row_num, column=col_num, padx=grid_padx, pady=grid_pady, sticky="nsew")
                group_canvas.grid_columnconfigure(col_num, weight=1)
                buttons[option_key] = button
                
                # ⚡ WYSIWYG: Only expose the FIRST button for resizing.
                # This allows the handles to target parent layout.width/height
                if idx == 0 and path:
                    button._oca_path = path 
                
                col_num += 1
                if col_num >= max_cols:
                    col_num, row_num = 0, row_num + 1

            update_button_styles()

            if path and state_mirror_engine:
                if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [MQTT] Registering toggler at path '{path}'")
                topic = state_mirror_engine.register_widget(path, selected_keys_var, base_mqtt_topic_from_path, config)
                
                def on_gui_change():
                    if BUILDER_DEBUG: builder_logger.debug(f"⚡🔴📡 [EVENT] Toggler '{label}' GUI change. Broadcasting to MQTT.")
                    state_mirror_engine.broadcast_gui_change_to_mqtt(path)
                
                bind_variable_trace(selected_keys_var, on_gui_change)
                selected_keys_var.trace_add("write", update_button_styles)
                
                if subscriber_router and topic:
                    if BUILDER_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing to topic: {topic}")
                    subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
                
                if BUILDER_DEBUG: builder_logger.trace(f"🔄⏳🔋 [STATE] Initializing widget state from cache/broker for '{path}'")
                state_mirror_engine.initialize_widget_state(path)

            redraw_labels()
            if BUILDER_DEBUG: builder_logger.success(f"✅🆗🔘 [SUCCESS] The button toggler group '{label}' has materialized!")
            return group_canvas
            
        except Exception as e:
            if BUILDER_DEBUG:
                builder_logger.exception(f"❌🚫🛑 [ERROR] Critical failure creating toggler group '{label}'")
            return None
