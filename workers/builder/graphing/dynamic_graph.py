# data_graphing/dynamic_graph.py
# Modularized FluxPlotter Graph Component.
# Version 20260315.Modular.1

import tkinter as tk
from collections import deque
import time
from typing import Dict, Any

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True
from workers.logger.logger import builder_logger
from managers.configini.config_reader import Config
app_constants = Config.get_instance()

from . import graph_builder, graph_styler, graph_interactor, graph_updater
from workers.styling.style import THEMES, DEFAULT_THEME
from managers.Display.transparency.transparency_mixin import TransparencyMixin
from managers.Display.transparency.transparency import TransparencyManager

# --- EXTRACTED CORE MIXINS ---
from .core.graph_patina_mixin import GraphPatinaMixin
from .core.graph_throttle_mixin import GraphThrottleMixin
from .core.graph_interaction_mixin import GraphInteractionMixin
from .core.graph_state_mixin import GraphStateMixin

class FluxPlotter(
    tk.Frame,
    TransparencyMixin,
    GraphPatinaMixin,
    GraphThrottleMixin,
    GraphInteractionMixin,
    GraphStateMixin
):
    """
    A high-performance Matplotlib graph widget refactored into modular components.
    """

    def __init__(self, parent, config: Dict[str, Any], base_mqtt_topic_from_path: str, widget_id: str, builder_instance=None, **kwargs):
        self.subscriber_router = kwargs.pop("subscriber_router", None)
        self.state_mirror_engine = kwargs.pop("state_mirror_engine", None)
        super().__init__(parent, **kwargs)

        self.widget_config, self.base_mqtt_topic_from_path, self.widget_id, self.instance = config, base_mqtt_topic_from_path, widget_id, builder_instance
        self.lines, self.x_data, self.y_data, self.datasets_config = {}, {}, {}, {}
        self.dataset_vars, self.settings_vars, self.marker_objects = {}, {}, []
        self.marker_var = tk.StringVar()
        self.dragging_marker, self.highlighted_marker, self.saved_style = None, None, {}

        self._initialize_throttle()
        self.fig, self.ax, self.canvas = graph_builder.create_base_plot(self, config)
        
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        self.theme_colors = colors
        self.configure(bg=colors["bg"])
        tk_canvas = self.canvas.get_tk_widget()
        tk_canvas.configure(bg=colors["bg"], highlightthickness=0)
        
        TransparencyManager.apply_transparency(self, tk_canvas, config, self.instance)

        if self.state_mirror_engine:
            self._initialize_state_mirroring()
            self._initialize_marker_mirroring()

        self._init_plot_elements()
        self._init_dataset_config()
        self._load_initial_data()

        self.bind("<Configure>", self._on_resize_event)
        self.canvas.mpl_connect('pick_event', self._on_pick)
        self.canvas.mpl_connect('motion_notify_event', self._on_motion)
        self.canvas.mpl_connect('button_release_event', self._on_marker_release)

    def render(self): self._on_patina_update()
    def _draw(self): self._schedule_update()

    def _init_plot_elements(self):
        graph_styler.apply_style(self.ax, self.fig, self.widget_config, graph_styler.get_theme_style("dark"))
        graph_interactor.setup_interaction(self.fig, self.ax, self.widget_config, {"on_view_change": lambda x, y: None, "on_setting_change": lambda n, v: None, "on_add_marker": self._on_add_marker})
        for ds in self.widget_config.get("datasets", []):
            ds_id = ds.get("id")
            if ds_id:
                line, = self.ax.plot([], [], color=ds.get("style", {}).get("line_color") or "cyan", linewidth=1, label=ds.get("label", ds_id))
                self.lines[ds_id], self.x_data[ds_id], self.y_data[ds_id] = line, deque(maxlen=self.widget_config.get("buffer_size", 100)), deque(maxlen=self.widget_config.get("buffer_size", 100))

    def _init_dataset_config(self):
        for ds in self.widget_config.get("datasets", []):
            ds_id = ds.get("id")
            if ds_id:
                self.datasets_config[ds_id] = ds
                var = tk.StringVar(); self.dataset_vars[ds_id] = var
                path = f"{self.widget_id}/DATA/{ds_id}"
                self.state_mirror_engine.register_widget(path, var, self.base_mqtt_topic_from_path, {"type": "_PlotDataset"})
                var.trace_add("write", lambda *a, d_id=ds_id: self._on_dataset_var_change(d_id))
                if self.subscriber_router:
                    t = self.state_mirror_engine.get_widget_topic(path)
                    if t: self.subscriber_router.subscribe_to_topic(t, self.state_mirror_engine.sync_incoming_mqtt_to_gui)
                self.state_mirror_engine.initialize_widget_state(path)

    def _load_initial_data(self):
        for ds_id, ds in self.datasets_config.items():
            csv = ds.get("initial_csv_data")
            if csv: self.dataset_vars[ds_id].set(csv)

    def _on_resize_event(self, event):
        last_w, last_h = getattr(self, "_last_resize_dim", (0, 0))
        if abs(event.width - last_w) <= 2 and abs(event.height - last_h) <= 2: return
        self._last_resize_dim = (event.width, event.height)
        if hasattr(self, "_resize_timer") and self._resize_timer: self.after_cancel(self._resize_timer)
        self._resize_timer = self.after(200, lambda: self._perform_resize(event.width, event.height))

    def _perform_resize(self, w, h):
        self._resize_timer = None
        if hasattr(self, "fig") and w > 1 and h > 1:
            dpi = self.fig.get_dpi(); self.fig.set_size_inches(w / dpi, h / dpi)
            self._on_patina_update()

    def _on_marker_var_change(self, *args):
        data = self.marker_var.get()
        if not data: return
        for obj in self.marker_objects: obj.remove()
        self.marker_objects.clear()
        try:
            lines = data.strip().split("\n")
            if lines and "type" in lines[0].lower(): lines = lines[1:]
            for l in lines:
                ps = l.split(",")
                if len(ps) < 2: continue
                m_type, val, col, label = ps[0].lower().strip(), float(ps[1]), ps[2].strip() or "red", ps[4] if len(ps)>4 else ""
                obj = self.ax.axvline(x=val, color=col, linewidth=1, label=label, picker=5) if m_type == 'x' else self.ax.axhline(y=val, color=col, linewidth=1, label=label, picker=5)
                self.marker_objects.append(obj)
            self.canvas.draw_idle()
        except Exception: pass

    def _update_marker_value(self, l, v):
        d = self.marker_var.get()
        if not d: return
        ls = d.strip().split("\n"); nls = []; upd = False
        for line in ls:
            ps = line.split(",")
            if len(ps) >= 5 and ps[4].strip() == l: ps[1] = f"{v:.4f}"; nls.append(",".join(ps)); upd = True
            else: nls.append(line)
        if upd: self.marker_var.set("\n".join(nls))

    def _rename_marker(self, o, n):
        d = self.marker_var.get()
        if not d: return
        ls = d.strip().split("\n"); nls = []; upd = False
        for line in ls:
            ps = line.split(",")
            if len(ps) >= 5 and ps[4].strip() == o:
                if n.strip(): ps[4] = n; nls.append(",".join(ps)); upd = True
            else: nls.append(line)
        if upd: self.marker_var.set("\n".join(nls))

    def _on_add_marker(self, m_type, val):
        cur = self.marker_var.get(); line = f"{m_type},{val:.4f},red,1,UserMarker_{int(time.time())}"
        self.marker_var.set(f"{cur}\n{line}" if cur else line)
