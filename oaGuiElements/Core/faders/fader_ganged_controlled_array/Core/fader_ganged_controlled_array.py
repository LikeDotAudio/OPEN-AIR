# fader_ganged_controlled_array/fader_ganged_controlled_array.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized Ganged Controlled Array (GCA) Fader.

import tkinter as tk

from oaConfigurationManager.FileReaders.config_reader import Config

# --- Standard Debug Logging Setup ---

app_constants = Config.get_instance()

from oaGui.Methods.formatting.i18n_utils import get_text
from oaGui.Core.factory.base_widget_creator import BaseWidgetCreator

# --- EXTRACTED CORE MODULES ---
from oaGuiElements.Core.faders.fader_ganged_controlled_array.Core.gca_controller_mixin import GCAControllerMixin
from oaGuiElements.Core.faders.fader_ganged_controlled_array.Core.gca_interaction_mixin import GCAInteractionMixin
from oaGuiElements.Core.faders.fader_ganged_controlled_array.Core.gca_renderer_mixin import GCARendererMixin
from oaGui.Hooks.registry.registry_widget_store import RegistryWidgetStore
from oaGui.Workers.compositing.engine_visual_effects import EngineVisualEffects
from oaGui.Workers.compositing.sync_behavior import SyncBehavior
from oaStyle.Core.style import DEFAULT_THEME, THEMES

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
        self.label = get_text(config.get("label_active"), "Composite")
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
            value = float(channel_config[i].get("default", self.min_val)) if i < len(channel_config) else self.min_val
            label = channel_config[i].get("label", f"{i+1}") if i < len(channel_config) else f"{i+1}"

            var = tk.DoubleVar(value=value)
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
        self.canvas.bind("<Double-Button-1>", self._toggle_mode)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)
        self._draw()

@RegistryWidgetStore.register("_CompositeFader")
class BuilderFaderGangedControlledArrayCreator(BaseWidgetCreator, SyncBehavior):

    is_composite = True

    def _assemble_ui(self, parent_widget, config_data, context, **kwargs):
        """Assembles the GCA Fader UI."""
        ctx = context if context else type('obj', (object,), kwargs)()
        b_inst = getattr(ctx, 'builder_instance', None) or getattr(ctx, 'app_instance', None) or kwargs.get('builder_instance')

        path = config_data.get("path", "")
        s_engine = getattr(ctx, 'state_mirror_engine', None) or kwargs.get('state_mirror_engine')
        b_topic = getattr(ctx, 'base_mqtt_topic_from_path', None) or kwargs.get('base_mqtt_topic_from_path', "")
        s_router = getattr(ctx, 'subscriber_router', None) or kwargs.get('subscriber_router')

        frame = CompositeFaderFrame(parent_widget, config_data, path, s_engine, s_router, b_topic)

        if hasattr(b_inst, '_apply_transparency'):
            EngineVisualEffects.apply_transparency(frame, frame.canvas, config_data, b_inst)

        if path and s_engine:
            topic = s_engine.register_widget(path, frame.master_value, b_topic, config_data)
            if s_router and topic:
                s_router.subscribe_to_topic(topic, s_engine.sync_incoming_mqtt_to_gui)
            s_engine.initialize_widget_state(path)

            for i in range(frame.num_channels):
                child_path = f"{path}/ch_{i+1}"
                child_topic = s_engine.register_widget(child_path, frame.child_values[i], b_topic, config_data)
                if s_router and child_topic:
                    s_router.subscribe_to_topic(child_topic, s_engine.sync_incoming_mqtt_to_gui)
                s_engine.initialize_widget_state(child_path)

        return frame, frame.canvas

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        return BuilderFaderGangedControlledArrayCreator.build(parent_widget, config_data, context, **kwargs)

    def make_fader_ganged_controlled_array(self, parent_widget, config_data, context=None, **kwargs):
        return BuilderFaderGangedControlledArrayCreator.build(parent_widget, config_data, context, **kwargs)
