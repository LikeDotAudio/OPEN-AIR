# data_graphing/dynamic_graph.py
import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog
from collections import deque
import time
from typing import Dict, Any, List
import os
import inspect

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

from . import graph_builder
from . import graph_styler
from . import graph_interactor
from . import graph_updater
from workers.styling.style import THEMES, DEFAULT_THEME
from workers.Command_Router.mqtt.mqtt_topic_utils import get_topic
from managers.Display.transparency.transparency_mixin import TransparencyMixin
from managers.Display.transparency.transparency_manager import TransparencyManager

# Globals
current_version = "20260218.Optimization.2"

class FluxPlotter(tk.Frame, TransparencyMixin):
    """
    A Tkinter-compatible Matplotlib graph widget that dynamically renders
    plots with multiple datasets.
    OPTIMIZED: 30 FPS throttle and redundancy filter.
    """

    def __init__(self, parent, config: Dict[str, Any], base_mqtt_topic_from_path: str, widget_id: str, builder_instance=None, **kwargs):
        if BUILDER_DEBUG: builder_logger.debug(f"📊📈📉 [BUILDER] FluxPlotter '{widget_id}' is materializing in the GUI fabric.")
        self.subscriber_router = kwargs.pop("subscriber_router", None)
        self.state_mirror_engine = kwargs.pop("state_mirror_engine", None)
        super().__init__(parent, **kwargs)

        self.widget_config = config
        self.base_mqtt_topic_from_path = base_mqtt_topic_from_path
        self.widget_id = widget_id
        self.instance = builder_instance

        self.lines: Dict[str, Any] = {}
        self.x_data: Dict[str, deque] = {}
        self.y_data: Dict[str, deque] = {}
        self.datasets_config: Dict[str, Any] = {}
        self.dataset_vars: Dict[str, tk.StringVar] = {}
        self.settings_vars: Dict[str, tk.StringVar] = {}
        self.marker_var = tk.StringVar()
        self.marker_objects = []
        self.dragging_marker = None
        self.highlighted_marker = None
        self.saved_style = {}

        # Throttling & Redundancy
        self._update_pending = False
        self._pending_data = {} # dataset_id -> (x_vals, y_values)
        self._last_draw_time = 0
        self._THROTTLE_MS = 33 
        self._last_csv_data = {} # ⚡ REDUNDANCY FILTER
        self._last_settings_vals = {} # ⚡ TEXT CACHE

        if BUILDER_DEBUG: builder_logger.trace(f"🏗️📊📉 [CONSTRUCT] Creating base Matplotlib figure for '{widget_id}'")
        self.fig, self.ax, self.canvas = graph_builder.create_base_plot(self, config)
        
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        bg_color = colors["bg"]
        self.theme_colors = colors # For TransparencyManager fallback
        self.configure(bg=bg_color)
        tk_canvas = self.canvas.get_tk_widget()
        tk_canvas.configure(bg=bg_color, highlightthickness=0)
        
        # ⚡ MANDATORY: Apply Industrial Transparency via Manager
        # We pass the full config so TransparencyManager can find 'transparent' or 'style.background_color'
        if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to plotter '{widget_id}'")
        TransparencyManager.apply_transparency(self, tk_canvas, config, self.instance)
        if BUILDER_DEBUG: builder_logger.debug(f"✅🆗📉 [BUILDER] FluxPlotter '{self.widget_id}' has applied industrial transparency protocols.")

        if self.state_mirror_engine:
            if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [STATE] Initializing state mirroring for '{widget_id}'")
            self._initialize_state_mirroring()
            self._initialize_marker_mirroring()

        self._initialize_plot_elements()
        self._process_dataset_config()
        self._load_all_initial_data()

        self.bind("<Configure>", self._on_resize)
        self.canvas.mpl_connect('pick_event', self._on_pick)
        self.canvas.mpl_connect('motion_notify_event', self._on_motion)
        self.canvas.mpl_connect('button_release_event', self._on_marker_release)
        if BUILDER_DEBUG: builder_logger.success(f"✅🆗📊 [SUCCESS] FluxPlotter '{self.widget_id}' initialization sequence complete.")

    def render(self):
        """Hook for TransparencyManager to trigger redraw when background changes."""
        self._on_patina_update()

    def _on_patina_update(self):
        """⚡ HIGH-FIDELITY: Draws patina DETAILS inside Matplotlib Figure."""
        # 🛡️ REBUILD GUARD: Ignore updates while the parent builder is still reflowing the GUI layout.
        if getattr(self.instance, '_is_rebuilding', False):
            if BUILDER_DEBUG: builder_logger.trace(f"📈💹🔳 [SYNC] FluxPlotter '{self.widget_id}' deferred patina injection: Builder is rebuilding.")
            return

        if BUILDER_DEBUG: builder_logger.debug(f"📈💹🎨 [SYNC] FluxPlotter '{self.widget_id}' is injecting high-fidelity patina texture into the plot.")
        tk_canvas = self.canvas.get_tk_widget()
        
        # 0. Clear Blit Cache to ensure the next draw captures the new background
        fig_id = id(self.fig)
        if fig_id in graph_updater._bg_cache:
            if BUILDER_DEBUG: builder_logger.trace("❌🧹🖼️ [CACHE] Clearing blit cache for patina update.")
            del graph_updater._bg_cache[fig_id]

        # 1. Sync flat color fallback
        try:
            bg_hex = tk_canvas.cget("bg")
            if bg_hex:
                # If we have a patina image, we prefer transparency + figimage
                # Otherwise, we match the hex color.
                has_patina = hasattr(tk_canvas, 'panel_bg_pil_slice')
                self.fig.patch.set_facecolor(bg_hex)
                self.ax.set_facecolor(bg_hex)
                
                # ⚡ IMPROVED: If we have patina, ALWAYS hide the patches to let it show through
                # Also check for explicit transparent flag
                is_trans = self.widget_config.get("transparent") is True
                if not is_trans:
                    # Check nested style
                    style = self.widget_config.get("style", {})
                    if isinstance(style, dict):
                        is_trans = style.get("background_color") == "match_theme" or style.get("bg_color") == "match_theme"

                if has_patina or is_trans:
                    self.fig.patch.set_visible(False)
                    self.ax.patch.set_visible(False)
                else:
                    self.fig.patch.set_visible(True)
                    self.ax.patch.set_visible(True)
        except Exception:
            pass

        # 2. Sync texture details
        if hasattr(tk_canvas, 'panel_bg_pil_slice'):
            try:
                import numpy as np
                from PIL import Image
                slice_pil = tk_canvas.panel_bg_pil_slice
                
                # Get current figure size in pixels
                w_px, h_px = self.canvas.get_width_height()
                
                if w_px > 1 and h_px > 1:
                    if BUILDER_DEBUG: builder_logger.trace(f"🖼️📐✨ [SYNC] Resizing patina to {w_px}x{h_px} for figure injection.")
                    # Resize patina to match graph area exactly
                    resized_patina = slice_pil.resize((w_px, h_px), Image.Resampling.LANCZOS)
                    patina_array = np.array(resized_patina)
                    
                    # Clear previous background images
                    self.fig.images.clear()
                    
                    # Draw resized patina as background
                    # zorder -100 to stay behind grid/lines
                    self.fig.figimage(patina_array, 0, 0, zorder=-100, origin='upper')
                    
                    # ⚡ MANDATORY: If we have an injected image, make patches transparent
                    self.fig.patch.set_visible(False)
                    self.ax.patch.set_visible(False)
            except Exception as e:
                if BUILDER_DEBUG:
                    builder_logger.error(f"❌🚫🛑 [ERROR] FluxPlotter: Patina injection failed: {e}")

        # 3. Trigger Redraw
        if BUILDER_DEBUG: builder_logger.debug(f"📊📉✨ [REDRAW] FluxPlotter '{self.widget_id}' patina injection complete. Scheduling redraw.")
        self._force_redraw = True
        self._schedule_update()

    def _draw(self):
        self._schedule_update()

    def _schedule_update(self):
        if self._update_pending: return
        self._update_pending = True
        now = time.time() * 1000
        elapsed = now - self._last_draw_time
        delay = max(1, self._THROTTLE_MS - int(elapsed))
        self.after(delay, self._perform_scheduled_update)

    def _perform_scheduled_update(self):
        self._update_pending = False
        self._last_draw_time = time.time() * 1000
        has_changes = False
        for ds_id, (x_vals, y_vals) in self._pending_data.items():
            if ds_id in self.lines:
                if BUILDER_DEBUG: builder_logger.debug(f"💹📈✨ [DATA] FluxPlotter '{self.widget_id}' populating dataset '{ds_id}' with {len(x_vals)} points.")
                ds_config = self.datasets_config.get(ds_id, {})
                smoothing = int(ds_config.get("style", {}).get("smoothing", 0))
                graph_updater.load_initial_data(self.lines[ds_id], self.x_data[ds_id], self.y_data[ds_id], x_vals, y_vals, smoothing=smoothing)
                has_changes = True
        self._pending_data.clear()
        
        if has_changes or getattr(self, '_force_redraw', False):
            # ⚡ OPTIMIZATION: Use Fast Blit for data-only updates
            # This bypasses the expensive 'get_window_extent' text measurement cycle
            if not getattr(self, '_force_redraw', False):
                if BUILDER_DEBUG: builder_logger.trace(f"📊📉⚡ [RENDER] FluxPlotter '{self.widget_id}' performing fast blit redraw.")
                graph_updater.perform_fast_blit(self.ax, self.canvas, list(self.lines.values()))
            else:
                if BUILDER_DEBUG: builder_logger.debug(f"💹📊🔄 [RENDER] FluxPlotter '{self.widget_id}' performing full autoscale and redraw.")
                graph_updater.autoscale_and_redraw(self.ax, self.canvas)
            self._force_redraw = False

    def _on_dataset_var_change(self, dataset_id, *args):
        if dataset_id not in self.dataset_vars: return
        csv_data = self.dataset_vars[dataset_id].get()
        if not csv_data: return
        
        # ⚡ REDUNDANCY FILTER: Skip if data identical to last packet
        if self._last_csv_data.get(dataset_id) == csv_data: return
        self._last_csv_data[dataset_id] = csv_data
        if BUILDER_DEBUG: builder_logger.debug(f"📈💹📥 [MQTT] FluxPlotter '{self.widget_id}' received fresh CSV data for dataset '{dataset_id}'.")

        try:
            x_values, y_values = [], []
            lines = csv_data.strip().split("\n")
            if lines and "x" in lines[0].lower() and "y" in lines[0].lower(): lines = lines[1:]
            for line in lines:
                parts = line.strip().split(",")
                if len(parts) >= 2:
                    x_values.append(float(parts[0]))
                    y_values.append(float(parts[1]))
            self._pending_data[dataset_id] = (x_values, y_values)
            self._schedule_update()
        except Exception: pass

    def _on_pick(self, e):
        if e.artist not in self.marker_objects: return
        if e.mouseevent.dblclick:
            a = e.artist; lbl = a.get_text() if hasattr(a, 'get_text') else a.get_label()
            if lbl and not lbl.startswith("_"):
                new = simpledialog.askstring("Rename", "Label:", initialvalue=lbl, parent=self)
                if new is not None: self._rename_marker(lbl, new)
        else: self.dragging_marker = e.artist
    def _on_motion(self, e):
        if e.inaxes != self.ax:
            if self.highlighted_marker: self._restore_marker_style(self.highlighted_marker); self.highlighted_marker = None; self.canvas.draw_idle()
            return
        if self.dragging_marker:
            # Check for vertical vs horizontal line dragging
            if hasattr(self.dragging_marker, 'get_xdata'):
                xd = self.dragging_marker.get_xdata()
                yd = self.dragging_marker.get_ydata()
                if len(xd) == 2 and xd[0] == xd[1] and e.xdata is not None: 
                    # Vertical Marker
                    self.dragging_marker.set_xdata([e.xdata, e.xdata])
                elif len(yd) == 2 and yd[0] == yd[1] and e.ydata is not None:
                    # Horizontal Marker
                    self.dragging_marker.set_ydata([e.ydata, e.ydata])
            self.canvas.draw_idle(); return
        hit = None
        for m in self.marker_objects:
            c, _ = m.contains(e)
            if c: hit = m; break
        if hit:
            if self.highlighted_marker != hit:
                if self.highlighted_marker: self._restore_marker_style(self.highlighted_marker)
                self.highlighted_marker = hit; self._save_marker_style(hit); self._apply_highlight(hit); self.canvas.draw_idle()
        elif self.highlighted_marker: self._restore_marker_style(self.highlighted_marker); self.highlighted_marker = None; self.canvas.draw_idle()
    def _save_marker_style(self, m):
        self.saved_style = {}
        if hasattr(m, 'get_color'): self.saved_style['color'] = m.get_color()
        if hasattr(m, 'get_linewidth'): self.saved_style['linewidth'] = m.get_linewidth()
    def _restore_marker_style(self, m):
        if not self.saved_style: return
        try:
            if 'color' in self.saved_style: m.set_color(self.saved_style['color'])
            if 'linewidth' in self.saved_style and hasattr(m, 'set_linewidth'): m.set_linewidth(self.saved_style['linewidth'])
        except: pass
        self.saved_style = {}
    def _apply_highlight(self, m):
        try:
            m.set_color('yellow')
            if hasattr(m, 'set_linewidth'): m.set_linewidth(m.get_linewidth() + 2)
        except: pass
    def _on_marker_release(self, e):
        if self.dragging_marker:
            lbl = self.dragging_marker.get_label()
            if hasattr(self.dragging_marker, 'get_xdata'):
                xd = self.dragging_marker.get_xdata()
                yd = self.dragging_marker.get_ydata()
                if len(xd) == 2 and xd[0] == xd[1]: # Vertical
                    self._update_marker_value(lbl, xd[0])
                elif len(yd) == 2 and yd[0] == yd[1]: # Horizontal
                    self._update_marker_value(lbl, yd[0])
            self.dragging_marker = None

    def _update_marker_value(self, l, v):
        d = self.marker_var.get()
        if not d: return
        ls = d.strip().split("\n"); nls = []; upd = False
        for line in ls:
            ps = line.split(",")
            if len(ps) >= 5 and ps[4].strip() == l: 
                ps[1] = f"{v:.4f}"
                nls.append(",".join(ps))
                upd = True
            else: nls.append(line)
        if upd: self.marker_var.set("\n".join(nls))

    def _rename_marker(self, o, n):
        d = self.marker_var.get()
        if not d: return
        ls = d.strip().split("\n"); nls = []; upd = False
        for line in ls:
            ps = line.split(",")
            if len(ps) >= 5 and ps[4].strip() == o:
                if n.strip(): ps[4] = n; nls.append(",".join(ps))
                upd = True
            else: nls.append(line)
        if upd: self.marker_var.set("\n".join(nls))

    def _on_resize(self, event):
        if hasattr(self, "fig"):
            # ⚡ OPTIMIZATION: Only resize if the change is significant to avoid 'jiggling' loops
            last_w, last_h = getattr(self, "_last_resize_dim", (0, 0))
            if abs(event.width - last_w) <= 2 and abs(event.height - last_h) <= 2:
                return
            
            self._last_resize_dim = (event.width, event.height)
            if BUILDER_DEBUG: builder_logger.debug(f"📊💹📏 [LAYOUT] FluxPlotter '{self.widget_id}' detected resize to {event.width}x{event.height}. Scheduling reconfiguration.")
            
            if hasattr(self, "_resize_timer") and self._resize_timer: self.after_cancel(self._resize_timer)
            self._resize_timer = self.after(200, lambda: self._perform_resize(event.width, event.height))

    def _perform_resize(self, w, h):
        self._resize_timer = None
        if hasattr(self, "fig") and w > 1 and h > 1:
            if BUILDER_DEBUG: builder_logger.debug(f"📉💹📐 [LAYOUT] FluxPlotter '{self.widget_id}' executing resize to {w}x{h}.")
            dpi = self.fig.get_dpi()
            self.fig.set_size_inches(w / dpi, h / dpi)
            # ⚡ Re-inject patina on resize
            self._on_patina_update()

    def _initialize_marker_mirroring(self):
        path = f"{self.widget_id}/DATA/MARKERS"
        self.state_mirror_engine.register_widget(path, self.marker_var, self.base_mqtt_topic_from_path, {"type": "_GraphMarkers"})
        self.marker_var.trace_add("write", self._on_marker_var_change)
        self.marker_var.trace_add("write", lambda *a: self.state_mirror_engine.broadcast_gui_change_to_mqtt(path))
        if self.subscriber_router:
            t = self.state_mirror_engine.get_widget_topic(path)
            if t: self.subscriber_router.subscribe_to_topic(t, self.state_mirror_engine.sync_incoming_mqtt_to_gui)

    def _on_marker_var_change(self, *args):
        data = self.marker_var.get()
        if not data: return
        if BUILDER_DEBUG: builder_logger.debug(f"📊📈📍 [STATE] FluxPlotter '{self.widget_id}' markers are shifting in the digital aether.")
        for obj in self.marker_objects: obj.remove()
        self.marker_objects.clear()
        try:
            lines = data.strip().split("\n")
            if lines and "type" in lines[0].lower(): lines = lines[1:]
            for l in lines:
                ps = l.split(",")
                if len(ps) < 2: continue
                try: val = float(ps[1])
                except Exception as e:
                    if BUILDER_DEBUG: builder_logger.error(f"❌🚫🛑 [ERROR] Graph Marker: Invalid value '{ps[1]}' in line '{l}'")
                    continue
                
                col = ps[2].strip() or "red"
                m_type = ps[0].lower().strip()
                label = ps[4] if len(ps)>4 else ""
                
                if m_type == 'x':
                    obj = self.ax.axvline(x=val, color=col, linewidth=1, label=label, picker=5)
                    self.marker_objects.append(obj)
                elif m_type == 'y':
                    obj = self.ax.axhline(y=val, color=col, linewidth=1, label=label, picker=5)
                    self.marker_objects.append(obj)
                else:
                    if BUILDER_DEBUG: builder_logger.warning(f"⚠️🔔🚫 [STATE] Graph Marker: Unknown marker type '{m_type}' in line '{l}'")
            
            self.canvas.draw_idle()
            if BUILDER_DEBUG: builder_logger.success(f"✅🆗📍 [SUCCESS] FluxPlotter '{self.widget_id}' markers have been re-rendered.")
        except Exception as e:
            if BUILDER_DEBUG: builder_logger.exception(f"❌🚫🛑 [ERROR] Graph Marker Critical Error during refresh for '{self.widget_id}'")
    def _initialize_state_mirroring(self):
        ss = ["show_grid", "xlim", "ylim", "title", "x_label", "y_label"]
        for s in ss:
            var = tk.StringVar(); self.settings_vars[s] = var
            path = f"{self.widget_id}/settings/{s}"
            self.state_mirror_engine.register_widget(path, var, self.base_mqtt_topic_from_path, {"type": "_GraphSetting"})
            var.trace_add("write", lambda *a, name=s: self._on_setting_var_change(name))
            var.trace_add("write", lambda *a, p=path: self.state_mirror_engine.broadcast_gui_change_to_mqtt(p))
            if self.subscriber_router:
                t = self.state_mirror_engine.get_widget_topic(path)
                if t: self.subscriber_router.subscribe_to_topic(t, self.state_mirror_engine.sync_incoming_mqtt_to_gui)
            self.state_mirror_engine.initialize_widget_state(path)
    def _on_setting_var_change(self, setting):
        v = self.settings_vars[setting].get()
        if not v: return
        
        # ⚡ OPTIMIZATION: Check if the value actually changed to prevent Matplotlib text measurement spam
        if self._last_settings_vals.get(setting) == v: return
        self._last_settings_vals[setting] = v

        try:
            if setting == "xlim": xmin, xmax = map(float, v.split(",")); self.ax.set_xlim(xmin, xmax)
            elif setting == "ylim": ymin, ymax = map(float, v.split(",")); self.ax.set_ylim(ymin, ymax)
            elif setting == "show_grid": self.ax.grid(v.lower() == "true")
            elif setting == "title": self.ax.set_title(v)
            elif setting == "x_label": self.ax.set_xlabel(v)
            elif setting == "y_label": self.ax.set_ylabel(v)
            # ⚡ NO DRAW IDLE HERE: Let the scheduler handle it to prevent redundancy
            self._force_redraw = True; self._schedule_update()
        except: pass
    def _initialize_plot_elements(self):
        graph_styler.apply_style(self.ax, self.fig, self.widget_config, graph_styler.get_theme_style("dark"))
        callbacks = {"on_view_change": lambda x, y: None, "on_setting_change": lambda n, v: None, "on_add_marker": self._on_add_marker}
        graph_interactor.setup_interaction(self.fig, self.ax, self.widget_config, callbacks)
        for ds in self.widget_config.get("datasets", []):
            ds_id = ds.get("id")
            if ds_id:
                col = ds.get("style", {}).get("line_color") or "cyan"
                line, = self.ax.plot([], [], color=col, linewidth=1, label=ds.get("label", ds_id))
                self.lines[ds_id] = line
                self.x_data[ds_id] = deque(maxlen=self.widget_config.get("buffer_size", 100))
                self.y_data[ds_id] = deque(maxlen=self.widget_config.get("buffer_size", 100))
    def _process_dataset_config(self):
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
    def _load_all_initial_data(self):
        for ds_id, ds in self.datasets_config.items():
            csv = ds.get("initial_csv_data")
            if csv: self.dataset_vars[ds_id].set(csv)
    def load_initial_data(self, dataset_id, x_vals, y_vals):
        self._pending_data[dataset_id] = (x_vals, y_vals); self._schedule_update()
    def update_plot(self, dataset_id, x_new, y_new):
        self.x_data[dataset_id].append(x_new); self.y_data[dataset_id].append(y_new); self._schedule_update()
    def clear_plot(self, dataset_id=None):
        ids = [dataset_id] if dataset_id else self.lines.keys()
        for d_id in ids:
            if d_id in self.lines: graph_updater.clear_plot_data(self.lines[d_id], self.x_data[d_id], self.y_data[d_id])
        self._force_redraw = True; self._schedule_update()

    def _on_view_change(self, xlim, ylim):
        """Callback for zoom/pan events."""
        # Optional: Sync to MQTT or other widgets
        pass

    def _on_setting_change(self, name, value):
        """Callback for setting changes from the context menu."""
        # Optional: React to specific setting changes
        pass

    def _on_add_marker(self, m_type, val):
        if LOCAL_DEBUG: logger.debug(f"📉💹 FluxPlotter '{self.widget_id}' adding new {m_type}-marker at position {val:.4f}.")
        cur = self.marker_var.get(); new_l = f"UserMarker_{int(time.time())}"; line = f"{m_type},{val:.4f},red,1,{new_l}"
        self.marker_var.set(f"{cur}\n{line}" if cur else line)
