# fader_ganged_controlled_array/fader_ganged_controlled_array.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized Ganged Controlled Array (GCA) Fader.

import tkinter as tk
from tkinter import ttk
from loguru import logger

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = False    
from oaLogging.Core.logger import builder_logger
from oaConfiguration.FileReaders.config_reader import Config
app_constants = Config.get_instance()

from oaStyle.Core.style import THEMES, DEFAULT_THEME
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
from oaGuiManager.Core.transparency.transparency import TransparencyManager
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry

# --- EXTRACTED CORE MODULES ---
from oaGuiElements.Core.faders.fader_ganged_controlled_array.Core.gca_controller_mixin import GCAControllerMixin
from oaGuiElements.Core.faders.fader_ganged_controlled_array.Core.gca_renderer_mixin import GCARendererMixin
from oaGuiElements.Core.faders.fader_ganged_controlled_array.Core.gca_interaction_mixin import GCAInteractionMixin

MIN_CHANNEL_WIDTH = 40

class CompositeFaderFrame(
    tk.Frame,
    GCAControllerMixin,
    GCARendererMixin,
    GCAInteractionMixin
):
    def __init__(self, master, config, path, state_mirror_engine, subscriber_router, base_mqtt_topic):
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        self.bg_color = colors.get("bg", "#2b2b2b")
        self.track_col = colors.get("secondary", "#444444")
        self.handle_col = colors.get("fg", "#dcdcdc")
        self.accent_col = colors.get("accent", "#f4902c")
        
        super().__init__(master, bg=self.bg_color, bd=0, highlightthickness=0)
        
        self.widget_config = config
        self.path = path
        self.state_mirror_engine = state_mirror_engine
        self.subscriber_router = subscriber_router
        self.base_mqtt_topic = base_mqtt_topic
        
        # Configuration
        self.min_val = float(config.get("value_min", 0.0))
        self.max_val = float(config.get("value_max", 100.0))
        self.num_channels = int(config.get("num_channels", 4))
        self.label = config.get("label_active", "Composite")
        self.is_rgb = config.get("is_rgb", False)
        
        # Visual Config
        layout_config = config.get("layout", {})
        requested_w = int(layout_config.get("width", config.get("width", 100)))
        self.req_width = max(requested_w, self.num_channels * MIN_CHANNEL_WIDTH)
        self.req_height = int(layout_config.get("height", config.get("height", 400)))
        self.width, self.height = self.req_width, self.req_height
        
        self.show_ticks = config.get("show_ticks", True)
        self.tick_thickness = int(config.get("tick_thickness", 1))
        self.tick_color = config.get("tick_color", "light grey")
        self.tick_interval = config.get("tick_interval", None)

        self.show_channel_labels = config.get("channel_labels_visible", True)
        self.channel_labels_pos = config.get("channel_labels_position", "bottom").lower()
        self.channel_labels_rotation = config.get("channel_labels_rotation", 0)

        # State
        self.mode = "macro" 
        self._lock_sync = False
        self.master_value = tk.DoubleVar(value=self.min_val)
        self.child_values, self.child_offsets, self.channel_labels = [], [], []
        
        # Initialize Children
        channel_config = config.get("channels", [])
        for i in range(self.num_channels):
            val = float(channel_config[i].get("default", self.min_val)) if i < len(channel_config) else self.min_val
            label = channel_config[i].get("label", f"{i+1}") if i < len(channel_config) else f"{i+1}"
            
            var = tk.DoubleVar(value=val)
            self.child_values.append(var)
            self.child_offsets.append(0.0)
            self.channel_labels.append(label)
            
            if self.path:
                self.state_mirror_engine.register_widget(f"{self.path}/ch_{i+1}", var, self.base_mqtt_topic, config)
            var.trace_add("write", lambda *args, idx=i: self._on_child_var_change(idx))

        self.master_value.trace_add("write", self._on_master_var_change)
        self._update_master_from_children(broadcast=False)
        self._recalculate_offsets()

        # UI
        self.canvas = tk.Canvas(self, width=self.width, height=self.height, bg=self.bg_color, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Interaction State
        self.dragging_master = False
        self.dragging_child = -1
        self.start_y, self.start_val = 0, 0
        
        # Bindings
        self.canvas.bind("<Button-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Button-3>", self._toggle_mode) 
        self.canvas.bind("<Double-Button-1>", self._toggle_mode) 
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

        self._draw()

@WidgetRegistry.register("_CompositeFader")
class BuilderFaderGangedControlledArrayCreator(TransparencyMixin):
    
    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        label = config_data.get("label_active", "Composite")
        path = config_data.get("path", "")
        
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            builder_instance = context.builder_instance
        else:
            state_mirror_engine = kwargs.get("state_mirror_engine")
            subscriber_router = kwargs.get("subscriber_router")
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path", "")
            builder_instance = kwargs.get("builder_instance")

        frame = CompositeFaderFrame(parent_widget, config_data, path, state_mirror_engine, subscriber_router, base_mqtt_topic_from_path)
        
        if hasattr(builder_instance, '_apply_transparency'):
            TransparencyManager.apply_transparency(frame, frame.canvas, config_data, builder_instance)
        
        if path and state_mirror_engine:
            topic = state_mirror_engine.register_widget(path, frame.master_value, base_mqtt_topic_from_path, config_data)
            if subscriber_router and topic:
                subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
            state_mirror_engine.initialize_widget_state(path)
            
            for i in range(frame.num_channels):
                child_path = f"{path}/ch_{i+1}"
                child_topic = state_mirror_engine.register_widget(child_path, frame.child_values[i], base_mqtt_topic_from_path, config_data)
                if subscriber_router and child_topic:
                    subscriber_router.subscribe_to_topic(child_topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
                state_mirror_engine.initialize_widget_state(child_path)

        return frame

    def make_fader_ganged_controlled_array(self, parent_widget, config_data, context=None, **kwargs):
        return BuilderFaderGangedControlledArrayCreator.make(parent_widget, config_data, context, builder_instance=self, **kwargs)
