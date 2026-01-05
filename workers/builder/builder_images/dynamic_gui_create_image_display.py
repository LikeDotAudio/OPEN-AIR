# workers/builder/dynamic_gui_create_image_display.py

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from managers.configini.config_reader import Config                                                                          

app_constants = Config.get_instance() # Get the singleton instance      
from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args 
import os
from workers.setup.path_initializer import GLOBAL_PROJECT_ROOT

from workers.mqtt.mqtt_topic_utils import get_topic # Import get_topic

class ImageDisplayCreatorMixin:
    def _create_image_display(self, parent_widget, config_data, **kwargs): # Updated signature
        """Creates an image display widget that is state-aware."""
        current_function_name = "_create_image_display"
        
        # Extract arguments from config_data
        label = config_data.get("label_active")
        config = config_data # config_data is the config
        path = config_data.get("path")
        
        # Access global context directly from self
        state_mirror_engine = self.state_mirror_engine
        subscriber_router = self.subscriber_router
        base_mqtt_topic_from_path = self.state_mirror_engine.base_topic if self.state_mirror_engine else ""

        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"🔬⚡️ Entering '{current_function_name}' to render an image for '{label}'.",
                **_get_log_args()
            )

        frame = ttk.Frame(parent_widget) # Use parent_widget here

        if label:
            ttk.Label(frame, text=label).pack(side=tk.TOP, pady=(0, 5))

        image_path_var = tk.StringVar(value=config.get("value_default", ""))
        image_label = ttk.Label(frame)
        image_label.pack(side=tk.LEFT)

        def update_image(*args):
            """Loads and displays the image from the path in the StringVar."""
            image_path_relative = image_path_var.get()
            if not image_path_relative:
                image_label.config(image=None, text="No image path provided.")
                return

            image_path_absolute = os.path.join(GLOBAL_PROJECT_ROOT, image_path_relative)

            try:
                pil_image = Image.open(image_path_absolute)
                # You might want to resize the image here if needed, e.g.:
                # pil_image = pil_image.resize((100, 100), Image.ANTIALIAS)
                tk_image = ImageTk.PhotoImage(pil_image)
                image_label.config(image=tk_image, text="")
                image_label.image = tk_image  # Keep a reference
            except FileNotFoundError:
                error_text = f"Image not found:\n{image_path_relative}"
                image_label.config(image=None, text=error_text)
                if app_constants.global_settings['debug_enabled']:
                    debug_logger(message=f"🖼️ {error_text}", **_get_log_args())
            except Exception as e:
                error_text = f"Error loading image:\n{e}"
                image_label.config(image=None, text=error_text)
                debug_logger(message=f"🔴 ERROR loading image: {e}", **_get_log_args())

        image_path_var.trace_add("write", update_image)
        update_image() # Initial update

        if path:
            widget_id = path
            state_mirror_engine.register_widget(widget_id, image_path_var, base_mqtt_topic_from_path, config)
            
            # Subscribe to the topic for incoming messages
            topic = get_topic("OPEN-AIR", self.state_mirror_engine.base_topic, widget_id)
            self.subscriber_router.subscribe_to_topic(topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui)
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"🔬 Widget '{label}' ({path}) registered with StateMirrorEngine.",
                    **_get_log_args()
                )
            # Initialize state from cache or broadcast
            state_mirror_engine.initialize_widget_state(path)
        
        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"✅ SUCCESS! The image for '{label}' has been rendered!",
                **_get_log_args()
            )
        return frame