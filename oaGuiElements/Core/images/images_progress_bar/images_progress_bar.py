# workers/builder/images_progress_bar/dynamic_guimake_images_progress_bar.py

import tkinter as tk
from tkinter import ttk

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

from oaComMQTT.Methods.mqtt_topic_utils import get_topic
import os
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry


@WidgetRegistry.register("ProgressBar", "_ProgressBar", "_SmartProgress")
class BuilderImagesProgressBarCreator(TransparencyMixin):
    def make_images_progress_bar(
        self, parent_widget, config_data, context=None, **kwargs
    ):  # Updated signature
        """Creates a progress bar widget that is state-aware."""
        current_function_name = "make_images_progress_bar"

        # Extract only widget-specific config from config_data
        label = config_data.get("label_active") or config_data.get("label", "")
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

        if LOCAL_DEBUG: logger.debug(f"🔬⚡️ Entering '{current_function_name}' to construct a progress indicator for '{label}'.")

        # Use tk.Canvas for transparency support
        canvas = tk.Canvas(
            parent_widget,
            bd=0,
            highlightthickness=0,
            relief="flat",
            height=30
        )
        
        # Apply Industrial Transparency
        if hasattr(self, '_apply_transparency'):
            self._apply_transparency(canvas, canvas, config_data, builder_instance)

        try:
            min_val = float(config.get("min", 0))
            max_val = float(config.get("max", 100))
            value_default = float(config.get("value_default", min_val))
            units = config.get("units", "")

            progress_var = tk.DoubleVar(value=value_default)

            progressbar = ttk.Progressbar(
                canvas,
                orient="horizontal",
                length=200,
                mode="determinate",
                maximum=max_val,
                variable=progress_var,
            )
            # Pack progressbar with side padding to reserve space for labels
            progressbar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(80 if label else 10, 60 if units else 10))

            def redraw_progress_text(*args):
                if not canvas.winfo_exists(): return
                canvas.delete("industrial_text")
                w = canvas.winfo_width()
                h = canvas.winfo_height()
                if w <= 1: return
                
                # Draw Main Label (Left)
                if label:
                    canvas.create_text(
                        10, h/2, text=f"{label}:", anchor="w",
                        fill="white", font=("Helvetica", 9), tags="industrial_text"
                    )
                
                # Draw Value Label (Right)
                current_value = progress_var.get()
                val_text = f"{current_value:.1f} {units}"
                canvas.create_text(
                    w - 10, h/2, text=val_text, anchor="e",
                    fill="white", font=("Helvetica", 9), tags="industrial_text"
                )

            def sync_bg():
                redraw_progress_text()
            
            canvas._draw = sync_bg
            canvas.render = sync_bg
            canvas.bind("<Configure>", redraw_progress_text, add="+")
            progress_var.trace_add("write", redraw_progress_text)

            if path:
                widget_id = path
                topic = state_mirror_engine.register_widget(
                    widget_id, progress_var, base_mqtt_topic_from_path, config
                )

                # Subscribe to the topic for incoming messages
                if subscriber_router and topic:
                    subscriber_router.subscribe_to_topic(
                        topic, state_mirror_engine.sync_incoming_mqtt_to_gui
                    )

                if LOCAL_DEBUG: logger.debug(f"🔬 Widget '{label}' ({path}) registered with StateMirrorEngine.")
                # Initialize state from cache or broadcast
                state_mirror_engine.initialize_widget_state(path)

            if LOCAL_DEBUG: logger.success(f"✅ SUCCESS! The progress bar '{label}' has been successfully rendered!")
            return canvas
        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception("❌ The progress bar '{label}' has failed to materialize! Error")
            return None
