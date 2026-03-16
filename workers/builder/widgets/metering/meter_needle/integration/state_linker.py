import tkinter as tk
import random

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

from workers.Command_Router.mqtt.mqtt_topic_utils import get_topic

class StateLinker:
    def __init__(self, state_mirror_engine, subscriber_router, config, base_topic_path):
        self.state_mirror_engine = state_mirror_engine
        self.subscriber_router = subscriber_router
        self.config = config
        self.base_topic_path = base_topic_path
        
        self.vu_value_var = tk.DoubleVar(value=self.config.value_default)
        self.vu_value_var_2 = tk.DoubleVar(value=self.config.value_default) if self.config.meter_mode == "stereo" else None

    def setup_links(self, animator):
        # Trace variables to trigger animation
        def on_value_change(*args):
            animator.update_target(self.vu_value_var.get())
        
        self.vu_value_var.trace_add("write", on_value_change)
        
        if self.config.meter_mode == "stereo":
            def on_value_change_2(*args):
                animator.update_target_2(self.vu_value_var_2.get())
            self.vu_value_var_2.trace_add("write", on_value_change_2)
            
        # Bind interactions for random testing
        self._bind_random_generators(animator.canvas)
        
        # Register with State Mirror
        if self.config.path:
            self._register_with_engine()

    def _bind_random_generators(self, canvas):
        def generate_random_value(event):
            random_val = random.uniform(self.config.min_val, self.config.max_val)
            self.vu_value_var.set(random_val)
            if self.config.meter_mode == "stereo":
                random_val_2 = random.uniform(self.config.min_val, self.config.max_val)
                self.vu_value_var_2.set(random_val_2)
            
            if self.state_mirror_engine:
                self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.config.path)
                if self.config.meter_mode == "stereo":
                     self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.config.path + "_2")

        canvas.bind("<Button-2>", generate_random_value)
        canvas.bind("<B2-Motion>", generate_random_value)

    def _register_with_engine(self):
        widget_id = self.config.path
        
        # Channel 1
        topic = self.state_mirror_engine.register_widget(
            widget_id, self.vu_value_var, self.base_topic_path, self.config.config
        )
        if self.subscriber_router and topic:
            self.subscriber_router.subscribe_to_topic(
                topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui
            )
        
        # Channel 2 (Stereo)
        if self.config.meter_mode == "stereo":
            widget_id_2 = widget_id + "_2" 
            topic_2 = self.state_mirror_engine.register_widget(
                widget_id_2, self.vu_value_var_2, self.base_topic_path, self.config.config
            )
            if self.subscriber_router and topic_2:
                self.subscriber_router.subscribe_to_topic(
                    topic_2, self.state_mirror_engine.sync_incoming_mqtt_to_gui
                )

        if LOCAL_DEBUG: logger.debug(f"🔬 Widget '{self.config.label}' ({self.config.path}) registered with StateMirrorEngine.")
        
        # Initialize state
        self.state_mirror_engine.initialize_widget_state(self.config.path)
        if self.config.meter_mode == "stereo":
             self.state_mirror_engine.initialize_widget_state(self.config.path + "_2")
