# text_gui_dropdown_option/dynamic_guimake_text_gui_dropdown_option.py
#
# This file provides the BuilderTextGuiDropdownOptionCreator class for creating dropdown (Combobox) widgets in the GUI.
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
# Version 20260110.2115.2

import os
import tkinter as tk
from tkinter import ttk
import inspect
from decimal import Decimal, InvalidOperation 

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

from workers.Command_Router.mqtt.mqtt_topic_utils import get_topic
from managers.Display.transparency.transparency_mixin import TransparencyMixin

# --- Global Scope Variables ---
current_file = f"{os.path.basename(__file__)}"
current_version = "20260110.2115.2"
current_version_hash = 4321098765 # Calculated hash

# --- Constants ---
DEFAULT_PAD_X = 5
DEFAULT_PAD_Y = 2


class BuilderTextGuiDropdownOptionCreator(TransparencyMixin):
    """
    A mixin class that provides the functionality for creating a
    dropdown (Combobox) widget.
    """

    def _blend_colors(self, color1, color2, alpha=0.5):
        """Blends two hex colors together."""
        def hex_to_rgb(hex_str):
            hex_str = hex_str.lstrip('#')
            return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

        def rgb_to_hex(rgb):
            return '#%02x%02x%02x' % rgb

        if not color1 or color1 == "": color1 = "#000000"
        if not color2 or color2 == "": color2 = "#ffffff"

        try:
            r1, g1, b1 = hex_to_rgb(color1)
            r2, g2, b2 = hex_to_rgb(color2)

            r = int(r1 * (1 - alpha) + r2 * alpha)
            g = int(g1 * (1 - alpha) + g2 * alpha)
            b = int(b1 * (1 - alpha) + b2 * alpha)

            return rgb_to_hex((r, g, b))
        except Exception:
            return color1

    # Creates a dropdown menu (Combobox) widget for selecting from a list of options.
    # This method sets up a Tkinter Combobox, populates it with options from the configuration,
    # manages its selected value via a StringVar, and synchronizes its state via MQTT.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): Configuration for the dropdown widget.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     tk.Frame: The created frame containing the dropdown widget, or None on failure.
    def make_text_gui_dropdown_option(
        self, parent_widget, config_data, context=None, **kwargs
    ): 
        """Creates a dropdown menu for multiple choice options."""
        current_function_name = inspect.currentframe().f_code.co_name

        # Extract only widget-specific config from config_data
        label = config_data.get("label")
        config = config_data  # config_data is the config
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

        # 1. Debug Entry
        if LOCAL_DEBUG: logger.debug(f"🧪🏗️🖥️ Dropdown for '{label}'...")

        try:
            # Use tk.Canvas for transparency support
            sub_frame = tk.Canvas(
                parent_widget,
                bd=0,
                highlightthickness=0,
                relief="flat",
                height=30
            )
            
            # Apply Industrial Transparency
            if hasattr(self, '_apply_transparency'):
                self._apply_transparency(sub_frame, sub_frame, config_data, builder_instance)

            options_map = config.get("options", {})
            # Ensure options_map is a dictionary
            if isinstance(options_map, list):
                if LOCAL_DEBUG: logger.debug(f"⚠️ WARNING: 'options' for '{label}' in config is a list, expected a dictionary. Falling back to empty dict.")
                options_map = {} 

            # Helper to get the best display label
            def get_display_label(opt_data, default_key):
                # Prioritize 'label_active', then 'label', then fallback to key
                return opt_data.get("label_active") or opt_data.get("label") or default_key

            # Try to convert values to Decimal for numerical sorting, fall back to string sorting.
            sorted_options = sorted(
                options_map.items(),
                key=lambda item: str(item[1].get("value", item[0])),
            )

            # Populate the dropdown with labels and map them to values
            option_labels = [
                get_display_label(opt, key) for key, opt in sorted_options
            ]
            option_values = [opt.get("value", key) for key, opt in sorted_options]

            if LOCAL_DEBUG: logger.debug(f"🧐 Options loaded for '{label}': {option_labels}")

            # Determine initial selection:
            initial_value_from_config = config.get("value_default")
            initial_selected_value = None
            
            if initial_value_from_config is not None:
                initial_selected_value = initial_value_from_config
            else:
                initial_selected_option_entry = next(
                    (
                        opt
                        for key, opt in options_map.items()
                        if str(opt.get("selected", "no")).lower() in ["yes", "true"]
                    ),
                    None,
                )
                if initial_selected_option_entry:
                    initial_selected_value = initial_selected_option_entry.get("value")

            # If nothing is selected, and there are options, pick the first one
            if initial_selected_value is None and option_values:
                initial_selected_value = option_values[0]

            selected_value_var = tk.StringVar(value=initial_selected_value)

            # Set displayed_text_var based on the initial_selected_value
            initial_displayed_text = ""
            if initial_selected_value is not None:
                for key, opt in options_map.items():
                    if str(opt.get("value", key)) == str(initial_selected_value):
                        initial_displayed_text = get_display_label(opt, key)
                        break
            
            displayed_text_var = tk.StringVar(value=initial_displayed_text)

            # Store the currently selected key for transmit_command (needed for path building)
            self._current_selected_key_for_path = None
            if initial_selected_value:
                self._current_selected_key_for_path = next(
                    (
                        k
                        for k, v in options_map.items()
                        if str(v.get("value", k)) == str(initial_selected_value)
                    ),
                    None,
                )

            def update_displayed_text_from_value_var(*args):
                """Callback for when selected_value_var changes (e.g., from MQTT)."""
                new_value = selected_value_var.get()
                found_label = ""
                for key, opt in options_map.items():
                    if str(opt.get("value", key)) == str(new_value):
                        found_label = get_display_label(opt, key)
                        break
                displayed_text_var.set(found_label)
                if LOCAL_DEBUG: logger.debug(f"⚡ fluxing... Dropdown '{label}' visually updated to '{found_label}' (value: {new_value}) from MQTT.")

            selected_value_var.trace_add("write", update_displayed_text_from_value_var)

            def on_select(event):
                try:
                    selected_label = displayed_text_var.get()
                    
                    # Reverse lookup: Find key based on displayed label
                    selected_key = next(
                        (
                            key
                            for key, opt in options_map.items()
                            if get_display_label(opt, key) == selected_label
                        ),
                        None,
                    )
                    
                    if selected_key:
                        selected_value = options_map.get(selected_key, {}).get("value", selected_key)

                        # Update the StringVar directly. This will trigger the trace.
                        if selected_value_var.get() != str(selected_value):  
                            selected_value_var.set(selected_value)

                        if LOCAL_DEBUG: logger.debug(f"GUI ACTION: Publishing to '{path}' with value '{selected_value}' (Label: {selected_label})")
                        # Broadcast the change
                        self.state_mirror_engine.broadcast_gui_change_to_mqtt(path)
                        self._current_selected_key_for_path = selected_key 
                    else:
                        if LOCAL_DEBUG: logger.debug(f"⚠️ Warning: Could not find key for label '{selected_label}'")

                except ValueError:
                    logger.error("❌ Invalid selection in dropdown.")

            # Configure custom style for the dropdown
            clean_path = path.replace('/', '_') if path else "default"
            style_name = f"Dropdown.{clean_path}.TCombobox"
            style = ttk.Style()
            
            def update_style(bg_color):
                # Blend background with white (50%)
                blended_bg = self._blend_colors(bg_color, "#ffffff", 0.5)
                
                # Configure the Combobox style
                style.configure(style_name, 
                    fieldbackground=blended_bg, 
                    foreground="white", 
                    background=bg_color, # This is the 'arrow button' background in clam
                    arrowcolor="white", # This is supported by 'clam' theme
                    bordercolor=bg_color,
                    lightcolor=bg_color,
                    darkcolor=bg_color
                )
                
                # Map states for the background and foreground
                style.map(style_name, 
                    fieldbackground=[("readonly", blended_bg), ("disabled", bg_color)],
                    foreground=[("readonly", "white"), ("disabled", "grey")],
                    background=[("readonly", bg_color)],
                    arrowcolor=[("readonly", "white")]
                )

            update_style(sub_frame.cget("bg"))

            # Create a Combobox that uses the displayed_text_var for its text.
            dropdown = ttk.Combobox(
                sub_frame,
                textvariable=displayed_text_var,
                values=option_labels,
                state="readonly",
                style=style_name,
            )

            dropdown.bind("<<ComboboxSelected>>", on_select)
            # Add left padding if there is a label to avoid overlap
            padx_left = 80 if label else 10
            dropdown.pack(side=tk.LEFT, padx=(padx_left, DEFAULT_PAD_X))

            def redraw_dropdown_label(*args):
                if not sub_frame.winfo_exists(): return
                sub_frame.delete("industrial_text")
                w = sub_frame.winfo_width()
                h = sub_frame.winfo_height()
                if w <= 1: return
                
                if label:
                    sub_frame.create_text(
                        10, h/2, text=f"{label}:", anchor="w",
                        fill="white", font=("Helvetica", 9),
                        tags="industrial_text"
                    )

            def sync_bg():
                bg = sub_frame.cget("bg")
                update_style(bg)
                redraw_dropdown_label()
            
            sub_frame._draw = sync_bg
            sub_frame.render = sync_bg
            sub_frame.bind("<Configure>", redraw_dropdown_label, add="+")

            if path:
                widget_id = path
                # Register the StringVar with the StateMirrorEngine for MQTT updates
                topic = state_mirror_engine.register_widget(
                    widget_id, selected_value_var, base_mqtt_topic_from_path, config
                )

                # Subscribe to this widget's topic to receive updates
                if topic and self.subscriber_router:
                    self.subscriber_router.subscribe_to_topic(
                        topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui
                    )

                if LOCAL_DEBUG: logger.debug(f"🔬 Widget '{label}' ({path}) registered. State: {selected_value_var.get()}")
                # Broadcast initial state or load from cache
                state_mirror_engine.initialize_widget_state(path)
            
            return sub_frame

        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception("❌ Error in {current_function_name} for '{label}'"
                )
                logger.exception("💥 KABOOM! The dropdown for '{label}' has fallen into the abyss! Error")
            return None
