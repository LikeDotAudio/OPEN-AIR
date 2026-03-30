# images_image_display/images_image_display.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: images_image_oaGuiDefinitions/dynamic_guimake_images_image_display.py

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

from oaOchestration.Core.path_initializer import GLOBAL_PROJECT_ROOT
from oaComMQTT.Methods.mqtt_topic_utils import get_topic  # Import get_topic
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
from oaStyle.Core.style import THEMES, DEFAULT_THEME


class BuilderImagesImageDisplayCreator(TransparencyMixin):
    # Creates an image display widget that loads and displays images dynamically.
    # This method sets up a Tkinter label to display an image. The image path is managed
    # by a tkinter StringVar and can be updated via MQTT, allowing for dynamic image changes.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): Configuration for the image display.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     tk.Frame: The created frame containing the image display, or None on failure.
    def make_images_image_display(
        self,
        parent_widget,
        config_data,
        context=None,
        **kwargs
    ):  # Updated signature
        """Creates an image display widget that is state-aware."""
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️🖼️ [BUILDER] Entering make_images_image_display")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config_data}")

        current_function_name = "make_images_image_display"

        # Extract arguments from config_data
        label = config_data.get("label_active")
        config = config_data  # config_data is the config
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

        if BUILDER_DEBUG: builder_logger.debug(f"🔬⚡️🖼️ [BUILDER] Forging image display frame for '{label}' at path '{path}'.")

        frame = tk.Frame(parent_widget)  # Use parent_widget here
        
        # Apply Industrial Transparency
        if hasattr(self, '_apply_transparency'):
            if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to image frame.")
            self._apply_transparency(frame, None, config_data, builder_instance)

        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        bg_color = colors.get("bg", "#2b2b2b")

        if label:
            tk.Label(frame, text=label, fg="white").pack(side=tk.TOP, pady=(0, 5))

        image_path_var = tk.StringVar(value=config.get("value_default", ""))
        image_label = tk.Label(frame)
        image_label.pack(side=tk.LEFT)
        
        def sync_bg():
            if BUILDER_DEBUG: builder_logger.trace(f"🔄👻🎨 [SYNC] Syncing image frame labels to background.")
            bg = frame.cget("bg")
            for child in frame.winfo_children():
                if isinstance(child, tk.Label):
                    child.config(bg=bg)
        
        frame._draw = sync_bg

        def update_image(*args):
            """Loads and displays the image from the path in the StringVar."""
            image_path_relative = image_path_var.get()
            if not image_path_relative:
                if BUILDER_DEBUG: builder_logger.debug(f"🖼️⏳🌀 [DATA] No image path provided for '{label}'.")
                image_label.config(image=None, text="No image path provided.")
                return

            if BUILDER_DEBUG: builder_logger.info(f"🔄📂🖼️ [DATA] Updating image for '{label}': {image_path_relative}")
            image_path_absolute = os.path.join(GLOBAL_PROJECT_ROOT, image_path_relative)

            try:
                pil_image = Image.open(image_path_absolute)
                # You might want to resize the image here if needed, e.g.:
                # pil_image = pil_image.resize((100, 100), Image.ANTIALIAS)
                tk_image = ImageTk.PhotoImage(pil_image)
                image_label.config(image=tk_image, text="")
                image_label.image = tk_image  # Keep a reference
                if BUILDER_DEBUG: builder_logger.debug(f"🖼️🆗✅ [DATA] Image '{image_path_relative}' loaded successfully.")
            except FileNotFoundError:
                error_text = f"Image not found:\n{image_path_relative}"
                image_label.config(image=None, text=error_text)
                if BUILDER_DEBUG: builder_logger.error(f"🖼️❌🚫 [ERROR] {error_text}")
            except Exception as e:
                error_text = f"Error loading image:\n{e}"
                image_label.config(image=None, text=error_text)
                if BUILDER_DEBUG:
                    builder_logger.error(f"❌🚫🛑 [ERROR] failure loading image for '{label}': {e}")

        image_path_var.trace_add("write", update_image)
        update_image()  # Initial update

        if path:
            if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [MQTT] Registering image display at path '{path}'")
            widget_id = path
            topic = state_mirror_engine.register_widget(
                widget_id,
                image_path_var,
                base_mqtt_topic_from_path,
                config,
            )

            # Subscribe to the topic for incoming messages
            if subscriber_router and topic:
                if BUILDER_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing to topic: {topic}")
                subscriber_router.subscribe_to_topic(
                    topic,
                    state_mirror_engine.sync_incoming_mqtt_to_gui,
                )
            
            # Initialize state from cache or broadcast
            if BUILDER_DEBUG: builder_logger.trace(f"🔄⏳🔋 [STATE] Initializing image state from cache/broker.")
            state_mirror_engine.initialize_widget_state(path)

        if BUILDER_DEBUG: builder_logger.success(f"✅🆗🖼️ [SUCCESS] The image display '{label}' has materialized!")
        return frame
