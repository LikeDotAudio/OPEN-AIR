# images_animation_oaGuiDefinitions/dynamic_guimake_images_animation_display.py
#
# A mixin for creating an animation display widget from a GIF file.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20250821.200641.1

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageSequence
import os

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

from oaOchestration.Core.path_initializer import (
    GLOBAL_PROJECT_ROOT,
)  # Import GLOBAL_PROJECT_ROOT
from oaComMQTT.Methods.mqtt_topic_utils import get_topic  # Import get_topic
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin


class BuilderImagesAnimationDisplayCreator(TransparencyMixin):
    # Creates an animation display widget from a GIF file.
    # This method loads a GIF file, creates a sequence of frames, and displays them
    # on a Tkinter label. It handles cases where the GIF is not found by creating a placeholder.
    # The animation's frame index can be controlled via a tkinter IntVar and synchronized via MQTT.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): Configuration for the animation display.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     tk.Frame: The created frame containing the animation display, or None on failure.
    def make_images_animation_display(
        self, parent_widget, config_data, context=None, **kwargs
    ):  # Updated signature
        """Creates an animation display widget."""
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️🎞️ [BUILDER] Entering make_images_animation_display")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config_data}")

        current_function_name = "make_images_animation_display"

        # Extract widget-specific config from config_data
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

        if BUILDER_DEBUG: builder_logger.debug(f"🔬⚡️🎞️ [BUILDER] Animating display for '{label}' at path '{path}'.")

        frame = tk.Frame(parent_widget)  # Use parent_widget here
        
        # Apply Industrial Transparency
        if hasattr(self, '_apply_transparency'):
            if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to animation frame.")
            self._apply_transparency(frame, None, config_data, builder_instance)

        if label:
            tk.Label(frame, text=label, bg=frame.cget("bg"), fg="white").pack(side=tk.TOP, pady=(0, 5))

        gif_path_relative = config.get("gif_path", "")
        gif_path_absolute = os.path.join(GLOBAL_PROJECT_ROOT, gif_path_relative)

        if BUILDER_DEBUG: builder_logger.info(f"🔄📂🎞️ [DATA] Loading GIF animation: {gif_path_relative}")
        frames = []
        try:
            with Image.open(gif_path_absolute) as im:
                for frame_img in ImageSequence.Iterator(im):
                    frames.append(ImageTk.PhotoImage(frame_img.copy()))
            if BUILDER_DEBUG: builder_logger.debug(f"🎞️🆗✅ [DATA] Successfully extracted {len(frames)} frames from GIF.")
        except FileNotFoundError:
            if BUILDER_DEBUG: builder_logger.error(f"🎞️❌🚫 [ERROR] GIF not found at {gif_path_absolute}. Creating placeholder.")
            try:
                # Ensure the directory exists before saving the placeholder
                os.makedirs(os.path.dirname(gif_path_absolute), exist_ok=True)

                # Create a simple static placeholder image (PNG)
                placeholder_image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
                placeholder_filename = gif_path_absolute + ".png"  # Save as PNG
                placeholder_image.save(placeholder_filename)

                # Load the placeholder as a single frame
                placeholder_tk_image = ImageTk.PhotoImage(placeholder_image)
                frames.append(placeholder_tk_image)
                if BUILDER_DEBUG: builder_logger.info(f"☑️🖼️✨ [DATA] Created placeholder image at {placeholder_filename}")
            except Exception as e_placeholder:
                if BUILDER_DEBUG: builder_logger.error(f"🎞️❌🚫 [ERROR] failure creating placeholder image: {e_placeholder}")
                # If even placeholder creation fails, create a generic error label
                anim_label = tk.Label(
                    frame,
                    text=f"[Animation Error]\n{e_placeholder}",
                    fg="red",
                    bg=frame.cget("bg"),
                    wraplength=150,
                )
                anim_label.pack(side=tk.LEFT)
                return frame  # Exit early if critical failure
        except Exception as e:
            if BUILDER_DEBUG: builder_logger.error(f"🎞️❌🚫 [ERROR] failure loading animation for '{label}': {e}")
            # Fallback to an error label for other loading errors
            anim_label = tk.Label(
                frame,
                text=f"[Animation Error]\n{e}",
                fg="red",
                bg=frame.cget("bg"),
                wraplength=150,
            )
            anim_label.pack(side=tk.LEFT)
            return frame  # Exit early if critical failure

        anim_label = tk.Label(frame)
        anim_label.pack(side=tk.LEFT)
        
        def sync_bg():
            if BUILDER_DEBUG: builder_logger.trace(f"🔄👻🎨 [SYNC] Syncing animation frame labels to background.")
            bg = frame.cget("bg")
            for child in frame.winfo_children():
                if isinstance(child, tk.Label):
                    child.config(bg=bg)
        
        frame._draw = sync_bg

        if frames:
            anim_label.config(image=frames[0])  # Display the first frame or placeholder

        # Introduce a tk.IntVar to hold the current frame index
        frame_index_var = tk.IntVar(value=config.get("value_default", 0))
        if BUILDER_DEBUG: builder_logger.debug(f"🔋🎞️✨ [STATE] Initial frame index for '{label}': {frame_index_var.get()}")

        def _update_frame(*args):  # Add *args to accept trace arguments
            try:
                frame_index = frame_index_var.get()
                if 0 <= frame_index < len(frames):
                    if BUILDER_DEBUG: builder_logger.trace(f"🔄✨🎞️ [SYNC] Updating animation '{label}' to frame index: {frame_index}")
                    anim_label.config(image=frames[frame_index])
            except (ValueError, TypeError) as e:
                if BUILDER_DEBUG: builder_logger.error(f"🎞️❌🚫 [ERROR] failure updating animation frame for '{label}': {e}")

        frame_index_var.trace_add(
            "write", _update_frame
        )  # Bind _update_frame to the trace

        if path:
            if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [MQTT] Registering animation at path '{path}'")
            widget_id = path
            # Register the IntVar with the StateMirrorEngine
            topic = state_mirror_engine.register_widget(
                widget_id, frame_index_var, base_mqtt_topic_from_path, config
            )

            # Subscribe to the topic for incoming messages
            if subscriber_router and topic:
                if BUILDER_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing to topic: {topic}")
                subscriber_router.subscribe_to_topic(
                    topic, state_mirror_engine.sync_incoming_mqtt_to_gui
                )

            # Initialize state from cache or broadcast
            if BUILDER_DEBUG: builder_logger.trace(f"🔄⏳🔋 [STATE] Initializing animation state from cache/broker.")
            state_mirror_engine.initialize_widget_state(path)
            
        if BUILDER_DEBUG: builder_logger.success(f"✅🆗🎞️ [SUCCESS] The animation for '{label}' has materialized!")
        return frame

    # Callback function for updating the animation frame via incoming MQTT messages.
    def _on_animation_frame_update_mqtt(self, topic, payload):
        import orjson 

        try:
            payload_data = orjson.loads(payload)
            value = payload_data.get("val")

            # Extract widget path from topic
            expected_prefix = self.state_mirror_engine.calculate_topic("", self.base_mqtt_topic_from_path)
            if topic.startswith(expected_prefix):
                from oaComMQTT.Methods.mqtt_topic_utils import TOPIC_DELIMITER
                widget_path = topic[len(expected_prefix) :].strip(TOPIC_DELIMITER)
            else:
                return

            # Instead of calling update_func directly, find the registered tk_var and set its value
            full_topic = self.state_mirror_engine.calculate_topic(widget_path, self.base_mqtt_topic_from_path)
            if full_topic in self.state_mirror_engine.registered_widgets:
                tk_var = self.state_mirror_engine.registered_widgets[full_topic]["var"]
                tk_var.set(value)  # Set the tk.Variable, which triggers its trace

        except (orjson.JSONDecodeError, AttributeError) as e:
            logger.error(f"❌ Error processing animation MQTT update for {topic}: {e}. Payload: {payload}")
