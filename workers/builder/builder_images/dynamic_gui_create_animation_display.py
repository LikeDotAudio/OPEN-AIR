# workers/builder/dynamic_gui_create_animation_display.py

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageSequence
from managers.configini.config_reader import Config                                                                          

app_constants = Config.get_instance() # Get the singleton instance      
from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args
import os
from workers.setup.path_initializer import GLOBAL_PROJECT_ROOT # Import GLOBAL_PROJECT_ROOT
from workers.mqtt.mqtt_topic_utils import get_topic # Import get_topic

class AnimationDisplayCreatorMixin:
    def _create_animation_display(self, parent_frame, label, config, path, base_mqtt_topic_from_path, state_mirror_engine, subscriber_router):
        """Creates an animation display widget."""
        current_function_name = "_create_animation_display"
        self.base_mqtt_topic_from_path = base_mqtt_topic_from_path # Store as instance variable
        
        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"🔬⚡️ Entering '{current_function_name}' to animate the display for '{label}'.",
                **_get_log_args()
            )

        frame = ttk.Frame(parent_frame)

        if label:
            ttk.Label(frame, text=label).pack(side=tk.TOP, pady=(0, 5))

        gif_path_relative = config.get("gif_path", "")
        gif_path_absolute = os.path.join(GLOBAL_PROJECT_ROOT, gif_path_relative)
        
        frames = []
        try:
            with Image.open(gif_path_absolute) as im:
                for frame_img in ImageSequence.Iterator(im):
                    frames.append(ImageTk.PhotoImage(frame_img.copy()))
        except FileNotFoundError:
            debug_logger(message=f"🔴 GIF not found at {gif_path_absolute}. Creating placeholder.", **_get_log_args())
            try:
                # Ensure the directory exists before saving the placeholder
                os.makedirs(os.path.dirname(gif_path_absolute), exist_ok=True)
                
                # Create a simple static placeholder image (PNG)
                placeholder_image = Image.new('RGB', (100, 100), color = 'black')
                placeholder_filename = gif_path_absolute + ".png" # Save as PNG
                placeholder_image.save(placeholder_filename)
                
                # Load the placeholder as a single frame
                placeholder_tk_image = ImageTk.PhotoImage(placeholder_image)
                frames.append(placeholder_tk_image)
                debug_logger(message=f"☑️ INFO: Created placeholder image at {placeholder_filename}")
            except Exception as e_placeholder:
                debug_logger(message=f"🔴 ERROR creating placeholder image: {e_placeholder}", **_get_log_args())
                # If even placeholder creation fails, create a generic error label
                anim_label = ttk.Label(frame, text=f"[Animation Error]\n{e_placeholder}", fg="red", bg="black", wraplength=150)
                anim_label.pack(side=tk.LEFT)
                return frame # Exit early if critical failure
        except Exception as e:
            debug_logger(message=f"🔴 ERROR loading animation: {e}", **_get_log_args())
            # Fallback to an error label for other loading errors
            anim_label = ttk.Label(frame, text=f"[Animation Error]\n{e}", fg="red", bg="black", wraplength=150)
            anim_label.pack(side=tk.LEFT)
            return frame # Exit early if critical failure

        anim_label = ttk.Label(frame)
        anim_label.pack(side=tk.LEFT)
        
        if frames:
            anim_label.config(image=frames[0]) # Display the first frame or placeholder

        # Introduce a tk.IntVar to hold the current frame index
        frame_index_var = tk.IntVar(value=config.get("value_default", 0))

        def _update_frame(*args): # Add *args to accept trace arguments
            try:
                frame_index = frame_index_var.get()
                if 0 <= frame_index < len(frames):
                    anim_label.config(image=frames[frame_index])
            except (ValueError, TypeError) as e:
                if app_constants.global_settings['debug_enabled']:
                    debug_logger(message=f"🔴 ERROR updating animation frame: {e}", file=os.path.basename(__file__), function=current_function_name)

        frame_index_var.trace_add("write", _update_frame) # Bind _update_frame to the trace

        if path:
            widget_id = path
            # Register the IntVar with the StateMirrorEngine
            state_mirror_engine.register_widget(widget_id, frame_index_var, base_mqtt_topic_from_path, config)
            
            # Subscribe to the topic for incoming messages
            topic = get_topic("OPEN-AIR", base_mqtt_topic_from_path, widget_id)
            subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)

            # Initialize state from cache or broadcast
            state_mirror_engine.initialize_widget_state(path)

        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"✅ SUCCESS! The animation for '{label}' is ready to roll!",
                **_get_log_args()
            )
        return frame

    def _on_animation_frame_update_mqtt(self, topic, payload):
        import orjson # Imported here to avoid circular dependency or top-level import issues
        try:
            payload_data = orjson.loads(payload)
            value = payload_data.get('val')
            
            # Extract widget path from topic
            expected_prefix = get_topic("OPEN-AIR", self.base_mqtt_topic_from_path, "") # Construct expected prefix with new base topic
            if topic.startswith(expected_prefix):
                widget_path = topic[len(expected_prefix):].strip(TOPIC_DELIMITER)
            else:
                if app_constants.global_settings['debug_enabled']:
                    debug_logger(message=f"⚠️ Unexpected topic format for animation frame update: {topic}", **_get_log_args())
                return
            
            # Instead of calling update_func directly, find the registered tk_var and set its value
            # This will trigger the trace and the _update_frame function
            full_topic = get_topic("OPEN-AIR", self.base_mqtt_topic_from_path, widget_path)
            if full_topic in self.state_mirror_engine.registered_widgets:
                tk_var = self.state_mirror_engine.registered_widgets[full_topic]["var"]
                tk_var.set(value) # Set the tk.Variable, which triggers its trace
            else:
                if app_constants.global_settings['debug_enabled']:
                    debug_logger(message=f"⚠️ Animation widget not found in registered_widgets for path: {widget_path}", **_get_log_args())

        except (orjson.JSONDecodeError, AttributeError) as e:
            if app_constants.global_settings['debug_enabled']:
                debug_logger(message=f"❌ Error processing animation MQTT update for {topic}: {e}. Payload: {payload}", **_get_log_args())