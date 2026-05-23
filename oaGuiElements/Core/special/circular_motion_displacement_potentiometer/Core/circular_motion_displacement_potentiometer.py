# circular_motion_displacement_potentiometer/circular_motion_displacement_potentiometer.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized Circular Motion Draggable Potentiometer (CMDP).

import tkinter as tk

# --- Standard Debug Logging Setup ---
from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

# --- Specialized Modules ---
from oaGui.Hooks.registry.registry_widget_store import RegistryWidgetStore
from oaGui.Workers.compositing.sync_behavior import SyncBehavior

from .cmdp_channel_handler import CMDP_LTPObject
from .cmdp_file_handler import CMDPFileHandler
from .cmdp_group_handler import CMDPGroupHandler

# --- EXTRACTED CORE MODULES ---
from .cmdp_interaction_mixin import CMDPInteractionMixin
from .cmdp_renderer_mixin import CMDPRendererMixin
from .cmdp_tree import CMDPTreeManager


class CMDPWidget(
    tk.Frame,
    SyncBehavior,
    CMDPInteractionMixin,
    CMDPRendererMixin
):
    """Coordinator for the CMDP widget, delegating logic to specialized core modules."""

    def __init__(self, master, config, mixin_ref, **kwargs):
        self.path = kwargs.pop("path", config.get("path", ""))
        self.base_mqtt_topic = kwargs.pop("base_mqtt_topic_from_path", "")
        # ⚡ SRP COMPLIANCE: Absorb and discard lifecycle flags that aren't Frame properties
        self.initial_visible = kwargs.pop("initial_visible", True)

        super().__init__(master, **{k: v for k, v in kwargs.items() if k in ["bg", "background", "padx", "pady"]})

        self.widget_config, self.mixin_ref = config, mixin_ref
        self.faders, self.active_fader, self.hovered_fader = [], None, None
        self.tree_window, self.pop_tree = None, None
        self.center_x, self.center_y, self.near_radius, self.far_radius = 500, 500, 120, 380

        self.show_groups_var, self.show_channels_var = tk.BooleanVar(value=True), tk.BooleanVar(value=False)
        self.group_vars, self.group_color_vars, self.group_name_vars = {}, {}, {}
        self.group_buttons, self.group_labels = {}, {}

        self.gh = CMDPGroupHandler(self); self.fh = CMDPFileHandler(self)
        self.tm = CMDPTreeManager(self)
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1); self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1); self.grid_rowconfigure(1, weight=0)

        self.canvas = tk.Canvas(self, highlightthickness=0); self.canvas.grid(row=0, column=0, sticky="nsew")
        if self.mixin_ref and hasattr(self.mixin_ref, '_apply_transparency'):
            self.mixin_ref._apply_transparency(self, self.canvas, self.widget_config, self.mixin_ref)

        # Sidebar
        self.sidebar = tk.Frame(self, width=125); self.sidebar.grid(row=0, column=1, sticky="nsew"); self.sidebar.pack_propagate(False)
        self.sidebar_controls = tk.Frame(self.sidebar); self.sidebar_controls.pack(side=tk.TOP, fill=tk.X, pady=2)

        self.btn_toggle_groups = tk.Button(self.sidebar_controls, text="Groups", bg="#f4902c", fg="black", font=("Arial", 7, "bold"), bd=1, relief="flat", command=self.toggle_groups_pane)
        self.btn_toggle_groups.pack(side=tk.TOP, fill=tk.X, padx=5, pady=1)
        self.btn_toggle_groups.bind("<Button-3>", lambda e: self.gh.groups_menu.post(e.x_root, e.y_root))

        self.groups_pane = tk.Frame(self.sidebar); self.groups_pane.pack(side=tk.TOP, fill=tk.BOTH, expand=False)
        self.groups_container = tk.Frame(self.groups_pane); self.groups_container.pack(fill=tk.BOTH, expand=True)

        self.btn_toggle_channels = tk.Button(self, text="Channels", bg="#f4902c", fg="black", font=("Arial", 7, "bold"), bd=1, relief="flat", command=self.tm.toggle)
        self.btn_toggle_channels.place(relx=0.005, rely=0.005, anchor="nw")

        # Canvas Bindings
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.canvas.bind("<Button-1>", self.on_click); self.canvas.bind("<B1-Motion>", self.on_drag); self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-2>", self.on_mid_click); self.canvas.bind("<B2-Motion>", self.on_mid_drag); self.canvas.bind("<ButtonRelease-2>", self.on_release)
        self.canvas.bind("<MouseWheel>", self.on_scroll); self.canvas.bind("<Button-4>", self.on_scroll); self.canvas.bind("<Button-5>", self.on_scroll)
        self.canvas.bind("<Motion>", self.on_motion)

        # Control Bar
        self.ctrl_bar = tk.Frame(self); self.ctrl_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        tk.Button(self.ctrl_bar, text="Revert to Defaults", bg="#f4902c", font=("Arial", 8, "bold"), relief="flat", command=self.revert_to_defaults).pack(side=tk.LEFT, padx=10, pady=2)
        tk.Button(self.ctrl_bar, text="Import JSON", bg="#444", fg="white", font=("Arial", 8, "bold"), relief="flat", command=self.fh.import_json).pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(self.ctrl_bar, text="Export JSON", bg="#444", fg="white", font=("Arial", 8, "bold"), relief="flat", command=self.fh.export_json).pack(side=tk.LEFT, padx=5, pady=2)

        def sync_bg():
            bg = self.canvas.cget("bg")
            for f in [self.sidebar, self.sidebar_controls, self.groups_pane, self.groups_container, self.ctrl_bar]: f.config(bg=bg)
            self.draw_static_ui(); [f.render_fader_visuals() for f in self.faders]
        self._draw = sync_bg; self.draw_static_ui()

    def add_group_ui(self, n, c, initial_visible=True): self.gh.add_group_ui(n, c, initial_visible)
    def toggle_groups_pane(self):
        iv = not self.show_groups_var.get(); self.show_groups_var.set(iv)
        if iv: self.groups_pane.pack(side=tk.TOP, fill=tk.BOTH, after=self.sidebar_controls); self.btn_toggle_groups.config(text="Groups ON", bg="#f4902c", fg="black")
        else: self.groups_pane.pack_forget(); self.btn_toggle_groups.config(text="Groups OFF", bg="#444", fg="white")

    def revert_to_defaults(self):
        for i, f in enumerate(self.faders):
            configuration = self.widget_config.get("channels", [])[i]
            f.val_var.set(configuration.get("depth", 50.0)); f.rot_var.set(configuration.get("level", 50.0)); f.angle_var.set(configuration.get("angle", 0.0)); f.mute_var.set(False)
            if self.mixin_ref.state_mirror_engine:
                for p in ["value", "rot", "angle", "mute"]: self.mixin_ref.state_mirror_engine.broadcast_gui_change_to_mqtt(f"{self.path}/ch{i}/{p}")
            self.tm.refresh()

    def update_tree(self, f): self.tm.refresh()

    def refresh_pop_tree(self):
        """Public alias for the tree manager's refresh method, used by handlers."""
        if hasattr(self, 'tm'):
            self.tm.refresh()

@RegistryWidgetStore.register("_CMDP")
class BuilderCircularMotionDisplacementPotentiometerCreator:
    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        ctx = context if context else type('obj', (object,), kwargs)()
        b_inst = ctx.builder_instance if hasattr(ctx, 'builder_instance') else ctx.app_instance
        cmdp = CMDPWidget(parent_widget, config_data, b_inst, path=config_data.get("path"), base_mqtt_topic_from_path=ctx.base_mqtt_topic_from_path, **kwargs)

        if ctx.state_mirror_engine:
            for p, v in [("show_groups", cmdp.show_groups_var), ("show_channels", cmdp.show_channels_var)]:
                ctx.state_mirror_engine.register_widget(f"{cmdp.path}/{p}", v, ctx.base_mqtt_topic_from_path, {"type": "_CMDP_UI"})
                v.trace_add("write", lambda *a, path=f"{cmdp.path}/{p}": ctx.state_mirror_engine.broadcast_gui_change_to_mqtt(path))

        channels = config_data.get("channels", []); g_cfgs = { g["name"]: g for g in config_data.get("group_configs", []) }
        for i, chan in enumerate(channels):
            gn = chan.get("group", "Default"); g_cfg = g_cfgs.get(gn, {"color": "#00FF00", "visible": True})
            cmdp.add_group_ui(gn, g_cfg.get("color", "#00FF00"), initial_visible=g_cfg.get("visible", True))

            f_path = f"{cmdp.path}/ch{i}"
            v, r, a, m = tk.DoubleVar(value=chan.get("depth", 50)), tk.DoubleVar(value=chan.get("level", 50)), tk.DoubleVar(value=chan.get("angle", 0)), tk.BooleanVar(value=chan.get("mute", False))
            if ctx.state_mirror_engine:
                for p, var, t in [("value", v, "_CMDP_Val"), ("rot", r, "_CMDP_Rot"), ("angle", a, "_CMDP_Angle"), ("mute", m, "_GuiButtonToggle")]:
                    tp = f"{f_path}/{p}"; ctx.state_mirror_engine.register_widget(tp, var, ctx.base_mqtt_topic_from_path, {"type": t})
                    var.trace_add("write", lambda *a, path=tp: ctx.state_mirror_engine.broadcast_gui_change_to_mqtt(path))
                    topic = ctx.state_mirror_engine.get_widget_topic(tp)
                    if ctx.subscriber_router and topic: ctx.subscriber_router.subscribe_to_topic(topic, ctx.state_mirror_engine.sync_incoming_mqtt_to_gui)
                    ctx.state_mirror_engine.initialize_widget_state(tp)

            f = CMDP_LTPObject(cmdp.canvas, i, g_cfg.get("color", "#00FF00"), i, chan.get("name", f"Ch {i+1}"), v, r, a, m, cmdp.update_tree, cmdp)
            f.group_name = gn; cmdp.faders.append(f)

        return cmdp

    def make_circular_motion_displacement_potentiometer(self, parent_widget, config_data, context=None, **kwargs):
        return BuilderCircularMotionDisplacementPotentiometerCreator.make(parent_widget, config_data, context, builder_instance=self, **kwargs)
