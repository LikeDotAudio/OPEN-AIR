# data_graphing/graph_interactor.py
#
# This module provides functions for setting up interactive features on Matplotlib graphs, including zoom, pan, and hover annotations.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20250821.200641.1
from matplotlib.backend_bases import NavigationToolbar2
from matplotlib.patches import Rectangle
from matplotlib.ticker import ScalarFormatter
from typing import Dict, Any
import math
import datetime
import os
import pathlib

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

def update_annotation(event, ax, annot):
    """Updates the annotation box, vertical line, and intersection dots."""
    v_line = getattr(ax, "_hover_vline", None)
    dots = getattr(ax, "_hover_dots", [])

    if event.inaxes == ax and getattr(ax, "hover_enabled", True):
        import numpy as np
        data_text = []
        marker_text = []
        
        if v_line:
            v_line.set_xdata([event.xdata, event.xdata])
            v_line.set_visible(True)

        active_dot_count = 0
        for line in ax.lines:
            if not line.get_visible() or line == v_line: continue
            label = line.get_label()
            if not label or label.startswith("_"): continue
            
            if "Marker" in label or "MRK" in label:
                x_d, y_d = line.get_xdata(), line.get_ydata()
                if len(x_d) > 0 and np.all(x_d == x_d[0]):
                    marker_text.append(f"{label}: X={x_d[0]:.2f}")
                elif len(y_d) > 0 and np.all(y_d == y_d[0]):
                    marker_text.append(f"{label}: Y={y_d[0]:.2f}")
                continue

            x_d, y_d = line.get_xdata(), line.get_ydata()
            if len(x_d) == 0: continue
            x_arr = np.array(x_d)
            idx = (np.abs(x_arr - event.xdata)).argmin()
            val_x, val_y = x_arr[idx], y_d[idx]
            data_text.append(f"{label}: {val_y:.2f}")

            if active_dot_count < len(dots):
                dot = dots[active_dot_count]
                dot.set_data([val_x], [val_y])
                dot.set_color(line.get_color())
                dot.set_visible(True)
                active_dot_count += 1
            
        for i in range(active_dot_count, len(dots)): dots[i].set_visible(False)

        if data_text or marker_text:
            content = [f"X: {event.xdata:.2f}"]
            if data_text: content.extend(data_text)
            if marker_text:
                if data_text: content.append("---")
                content.extend(marker_text)
            annot.set_text("\n".join(content))
            annot.xy = (event.xdata, event.ydata)
            annot.set_visible(True)
            ax.figure.canvas.draw_idle()
    else:
        if annot.get_visible(): annot.set_visible(False)
        if v_line: v_line.set_visible(False)
        for d in dots: d.set_visible(False)
        ax.figure.canvas.draw_idle()

class ZoomPan:
    def __init__(self, ax, callbacks=None, on_context_menu=None):
        self.ax = ax
        self.callbacks = callbacks
        self.on_context_menu_callback = on_context_menu
        self.fig = ax.get_figure()
        self.press = None
        self.rect = None
        self.rect_start = None
        self.cur_xlim = self.cur_ylim = None
        self.axis_mode = self.pan_axis_mode = None
        self.initial_xlim = self.ax.get_xlim()
        self.initial_ylim = self.ax.get_ylim()
        self.fig.canvas.mpl_connect("button_press_event", self.on_press)
        self.fig.canvas.mpl_connect("button_release_event", self.on_release)
        self.fig.canvas.mpl_connect("motion_notify_event", self.on_motion)
        self.fig.canvas.mpl_connect("scroll_event", self.on_scroll)
        
    def update_initial_limits(self):
        self.initial_xlim, self.initial_ylim = self.ax.get_xlim(), self.ax.get_ylim()

    def _trigger_view_change(self):
        if self.callbacks and "on_view_change" in self.callbacks:
            self.callbacks["on_view_change"](self.ax.get_xlim(), self.ax.get_ylim())

    def on_press(self, event):
        if LOCAL_DEBUG: logger.debug(f"📊📈 graph_interactor: Button {event.button} pressed at ({event.xdata}, {event.ydata}).")
        if event.inaxes != self.ax:
            bbox = self.ax.bbox
            x, y = event.x, event.y
            is_bottom = (bbox.x0 <= x <= bbox.x1) and (bbox.y0 - 80 < y < bbox.y0)
            is_left = (bbox.y0 <= y <= bbox.y1) and (bbox.x0 - 80 < x < bbox.x0)
            is_right = (x > bbox.x1) and (bbox.y0 <= y <= bbox.y1)
            is_top = (y > bbox.y1) and (bbox.x0 <= x <= bbox.x1)

            if event.dblclick and event.button == 1:
                from tkinter import simpledialog
                changed = False
                if is_left:
                    v = simpledialog.askfloat("Limit", "Set X Min:", initialvalue=self.ax.get_xlim()[0])
                    if v is not None: self.ax.set_xlim(left=v); changed = True
                elif is_right:
                    v = simpledialog.askfloat("Limit", "Set X Max:", initialvalue=self.ax.get_xlim()[1])
                    if v is not None: self.ax.set_xlim(right=v); changed = True
                elif is_top:
                    v = simpledialog.askfloat("Limit", "Set Y Max:", initialvalue=self.ax.get_ylim()[1])
                    if v is not None: self.ax.set_ylim(top=v); changed = True
                elif is_bottom:
                    v = simpledialog.askfloat("Limit", "Set Y Min:", initialvalue=self.ax.get_ylim()[0])
                    if v is not None: self.ax.set_ylim(bottom=v); changed = True
                if changed: self.ax.figure.canvas.draw_idle(); self._trigger_view_change(); return

            if event.dblclick:
                self.ax.set_xlim(self.initial_xlim); self.ax.set_ylim(self.initial_ylim)
                self.ax.figure.canvas.draw(); self._trigger_view_change(); return

            if event.button == 1:
                if is_bottom or is_top: self.axis_mode = 'x'; self.press = (x, y); self.cur_xlim = self.ax.get_xlim()
                if is_left or is_right: self.axis_mode = 'y'; self.press = (x, y); self.cur_ylim = self.ax.get_ylim()
                return
            if event.button == 2:
                if is_bottom or is_top: self.pan_axis_mode = 'x'; self.press = (x, y); self.cur_xlim = self.ax.get_xlim()
                if is_left or is_right: self.pan_axis_mode = 'y'; self.press = (x, y); self.cur_ylim = self.ax.get_ylim()
                return
            return 
        
        if event.button == 2:
            # Main Area Pan: Store pixels and current limits
            self.cur_xlim, self.cur_ylim = self.ax.get_xlim(), self.ax.get_ylim()
            self.press = (event.x, event.y)
        elif event.button == 3:
            self.rect_start = (event.xdata, event.ydata)
            self.rect = Rectangle((event.xdata, event.ydata), 0, 0, linewidth=1, edgecolor='white', facecolor=(1, 1, 1, 0.2))
            self.ax.add_patch(self.rect); self.ax.figure.canvas.draw_idle()

    def on_release(self, event):
        if LOCAL_DEBUG: logger.debug(f"💹📉 graph_interactor: Button {event.button} released.")
        if self.axis_mode or self.pan_axis_mode:
            self.axis_mode = self.pan_axis_mode = self.press = None
            self._trigger_view_change(); return
        if self.press is not None and event.button == 2:
            self.press = None; self.ax.figure.canvas.draw(); self._trigger_view_change()
        if self.rect is not None and event.button == 3:
            x0, y0 = self.rect_start; x1, y1 = event.xdata, event.ydata
            self.rect.remove(); self.rect = self.rect_start = None
            if x0 is not None and x1 is not None and x0 != x1 and y0 != y1:
                 self.ax.set_xlim(min(x0, x1), max(x0, x1)); self.ax.set_ylim(min(y0, y1), max(y0, y1))
                 self.ax.figure.canvas.draw_idle(); self._trigger_view_change()
            else:
                 if self.on_context_menu_callback: self.on_context_menu_callback(event)
                 self.ax.figure.canvas.draw_idle()

    def on_motion(self, event):
        if self.axis_mode and self.press:
            x_start, y_start = self.press
            if self.axis_mode == 'x':
                dx = event.x - x_start; scale = max(0.1, 1.0 - (dx / 500.0))
                vmin, vmax = self.cur_xlim; center = (vmin + vmax) / 2
                span = ((vmax - vmin) / 2) * scale
                self.ax.set_xlim(center - span, center + span)
            elif self.axis_mode == 'y':
                dy = event.y - y_start; scale = max(0.1, 1.0 - (dy / 500.0))
                vmin, vmax = self.cur_ylim; center = (vmin + vmax) / 2
                span = ((vmax - vmin) / 2) * scale
                self.ax.set_ylim(center - span, center + span)
            self.ax.figure.canvas.draw_idle(); return

        if self.pan_axis_mode and self.press:
            x_start, y_start = self.press
            if self.pan_axis_mode == 'x' and self.ax.bbox.width > 0:
                dx = ((self.cur_xlim[1] - self.cur_xlim[0]) / self.ax.bbox.width) * (event.x - x_start)
                self.ax.set_xlim(self.cur_xlim[0] - dx, self.cur_xlim[1] - dx)
            elif self.pan_axis_mode == 'y' and self.ax.bbox.height > 0:
                dy = ((self.cur_ylim[1] - self.cur_ylim[0]) / self.ax.bbox.height) * (event.y - y_start)
                self.ax.set_ylim(self.cur_ylim[0] - dy, self.cur_ylim[1] - dy)
            self.ax.figure.canvas.draw_idle(); return

        if event.inaxes != self.ax: return
        if self.press is not None and event.button == 2 and not self.pan_axis_mode:
            # Main Area Pan: Use Pixels to avoid jitter
            x_start, y_start = self.press
            dx_pix, dy_pix = event.x - x_start, event.y - y_start
            w, h = self.ax.bbox.width, self.ax.bbox.height
            if w > 0 and h > 0:
                dx = ((self.cur_xlim[1] - self.cur_xlim[0]) / w) * dx_pix
                dy = ((self.cur_ylim[1] - self.cur_ylim[0]) / h) * dy_pix
                self.ax.set_xlim(self.cur_xlim[0] - dx, self.cur_xlim[1] - dx)
                self.ax.set_ylim(self.cur_ylim[0] - dy, self.cur_ylim[1] - dy)
                self.ax.figure.canvas.draw_idle()
        elif self.rect is not None:
            x0, y0 = self.rect_start; x1, y1 = event.xdata, event.ydata
            self.rect.set_width(abs(x1 - x0)); self.rect.set_height(abs(y1 - y0))
            self.rect.set_xy((min(x0, x1), min(y0, y1))); self.ax.figure.canvas.draw_idle()

    def on_scroll(self, event):
        if LOCAL_DEBUG: logger.debug(f"📈💹 graph_interactor: Scroll event detected ({event.button}). Scaling view.")
        if event.inaxes != self.ax: return
        f = 1 / 1.1 if event.button == "up" else 1.1
        cur_x, cur_y = self.ax.get_xlim(), self.ax.get_ylim()
        xd, yd = event.xdata, event.ydata
        if self.ax.get_xscale() == 'log':
            self.ax.set_xlim(xd * (cur_x[0]/xd)**f, xd * (cur_x[1]/xd)**f)
        else:
            self.ax.set_xlim((cur_x[0]-xd)*f + xd, (cur_x[1]-xd)*f + xd)
        if self.ax.get_yscale() == 'log':
            self.ax.set_ylim(yd * (cur_y[0]/yd)**f, yd * (cur_y[1]/yd)**f)
        else:
            self.ax.set_ylim((cur_y[0]-yd)*f + yd, (cur_y[1]-yd)*f + yd)
        self.ax.figure.canvas.draw(); self._trigger_view_change()

def setup_interaction(fig: object, ax: object, interaction_config: Dict[str, Any], callbacks: Dict[str, Any] = None):
    try:
        if LOCAL_DEBUG: logger.debug(f"📊💹 graph_interactor: Setting up interaction protocols for figure.")
        nav_config = interaction_config.get("Navigation", interaction_config)
        import tkinter as tk
        from tkinter import simpledialog, filedialog
        active_menu = [None]
        
        def close_menu(*args):
            if active_menu[0]:
                try: active_menu[0].unpost(); active_menu[0].destroy()
                except: pass
                active_menu[0] = None
        fig.canvas.get_tk_widget().bind("<Unmap>", close_menu)

        annot = None
        if nav_config.get("show_hover_value"):
            ax._hover_vline = ax.axvline(0, color='grey', linestyle='--', linewidth=1, alpha=0.7, visible=False, zorder=1)
            ax._hover_dots = [ax.plot([], [], 'o', markersize=6, visible=False, zorder=10)[0] for _ in range(10)]
            annot = ax.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points", 
                                bbox=dict(boxstyle="round", fc="w", alpha=0.9), arrowprops=dict(arrowstyle="->"), zorder=11)
            annot.set_visible(False)
            def on_hover(event): update_annotation(event, ax, annot)
            fig.canvas.mpl_connect("motion_notify_event", on_hover)

        def on_context_menu(event):
            try:
                close_menu()
                menu = tk.Menu(fig.canvas.get_tk_widget(), tearoff=0); active_menu[0] = menu
                
                # --- MARKERS ---
                m_menu = tk.Menu(menu, tearoff=0); menu.add_cascade(label="Markers", menu=m_menu)
                def av(): 
                    if callbacks and "on_add_marker" in callbacks and event.xdata is not None:
                        callbacks["on_add_marker"]('x', event.xdata)
                    else:
                        logger.warning("⚠️ Graph Interactor: Cannot add vertical marker (no callback or xdata)")
                def ah():
                    if callbacks and "on_add_marker" in callbacks and event.ydata is not None:
                        callbacks["on_add_marker"]('y', event.ydata)
                    else:
                        logger.warning("⚠️ Graph Interactor: Cannot add horizontal marker (no callback or ydata)")
                m_menu.add_command(label="Add Vertical Marker (X)", command=av)
                m_menu.add_command(label="Add Horizontal Marker (Y)", command=ah)

                # --- ISOLATE ---
                i_menu = tk.Menu(menu, tearoff=0); menu.add_cascade(label="Isolate", menu=i_menu)
                def _refresh_legend():
                    """Helper to draw legend outside top-right."""
                    try:
                        if ax.get_legend_handles_labels()[1]:
                            ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0.)
                            fig.tight_layout()
                        elif ax.get_legend():
                            ax.get_legend().remove()
                    except Exception as e:
                        logger.exception("❌ Graph Interactor: Legend refresh failed")

                def res_iso():
                    for l in ax.lines:
                        lb = l.get_label()
                        if lb and (lb.startswith("Marker") or lb.startswith("MRK")):
                            l.set_label("_nolegend_")
                        l.set_visible(True)
                    _refresh_legend()
                    fig.canvas.draw_idle()
                def do_iso(t):
                    for l in ax.lines:
                        l.set_visible(l == t)
                        lb = l.get_label()
                        if lb and (lb.startswith("Marker") or lb.startswith("MRK")):
                            l.set_label("_nolegend_")
                    _refresh_legend()
                    fig.canvas.draw_idle()
                i_menu.add_command(label="Reset Isolation (Show All)", command=res_iso)
                i_menu.add_separator()
                hl = False
                for l in ax.lines:
                    lb = l.get_label()
                    if not lb or lb.startswith("_") or "Marker" in lb or "MRK" in lb: continue
                    hl = True; i_menu.add_command(label=lb, command=lambda line=l: do_iso(line))
                if not hl: i_menu.add_command(label="No Datasets", state="disabled")

                # --- SHOW/HIDE ---
                sh_menu = tk.Menu(menu, tearoff=0); menu.add_cascade(label="Show / Hide", menu=sh_menu)
                def tl():
                    leg = ax.get_legend()
                    if leg: leg.remove()
                    else: _refresh_legend()
                    fig.canvas.draw_idle()
                sh_menu.add_command(label="Toggle Legend", command=tl)
                sh_menu.add_command(label="Toggle Grid", command=lambda: (ax.grid(), fig.canvas.draw_idle()))
                def tc():
                    ax.hover_enabled = not getattr(ax, "hover_enabled", True)
                    if not ax.hover_enabled:
                        annot.set_visible(False)
                        if hasattr(ax, "_hover_vline"): ax._hover_vline.set_visible(False)
                        for d in getattr(ax, "_hover_dots", []): d.set_visible(False)
                    fig.canvas.draw_idle()
                sh_menu.add_command(label="Toggle Cursor", command=tc)
                def ta():
                    v = not ax.get_xaxis().get_visible()
                    ax.get_xaxis().set_visible(v); ax.get_yaxis().set_visible(v); fig.canvas.draw_idle()
                sh_menu.add_command(label="Show Units / Axis", command=ta)

                # --- LABELS ---
                l_menu = tk.Menu(menu, tearoff=0); menu.add_cascade(label="Labels", menu=l_menu)
                l_menu.add_command(label="Toggle X Label", command=lambda: (ax.xaxis.label.set_visible(not ax.xaxis.label.get_visible()), fig.canvas.draw_idle()))
                l_menu.add_command(label="Toggle Y Label", command=lambda: (ax.yaxis.label.set_visible(not ax.yaxis.label.get_visible()), fig.canvas.draw_idle()))
                l_menu.add_separator()
                def tnx(): v = ax.get_xticklabels()[0].get_visible(); ax.tick_params(axis='x', labelbottom=not v); fig.canvas.draw_idle()
                def tny(): v = ax.get_yticklabels()[0].get_visible(); ax.tick_params(axis='y', labelleft=not v); fig.canvas.draw_idle()
                l_menu.add_command(label="Toggle X Numbers", command=tnx)
                l_menu.add_command(label="Toggle Y Numbers", command=tny)
                l_menu.add_separator()
                l_menu.add_command(label="Toggle X Scale", command=lambda: (ax.set_xscale('log' if ax.get_xscale()=='linear' else 'linear'), fig.canvas.draw_idle()))
                l_menu.add_command(label="Toggle Y Scale", command=lambda: (ax.set_yscale('log' if ax.get_yscale()=='linear' else 'linear'), fig.canvas.draw_idle()))

                # --- RENAME ---
                rn_menu = tk.Menu(menu, tearoff=0); menu.add_cascade(label="Rename", menu=rn_menu)
                def rn(attr):
                    try:
                        v = simpledialog.askstring("Rename", f"New {attr}:", initialvalue=getattr(ax, f"get_{attr}")())
                        if v: getattr(ax, f"set_{attr}")(v); fig.canvas.draw_idle()
                    except Exception as e:
                        logger.exception("❌ Graph Interactor: Rename failed")
                rn_menu.add_command(label="Chart Title", command=lambda: rn("title"))
                rn_menu.add_command(label="X-Axis Label", command=lambda: rn("xlabel"))
                rn_menu.add_command(label="Y-Axis Label", command=lambda: rn("ylabel"))

                # --- SET LIMITS ---
                sl_menu = tk.Menu(menu, tearoff=0); menu.add_cascade(label="Set Limits", menu=sl_menu)
                def sl(a, s):
                    try:
                        curr = ax.get_xlim() if a == 'x' else ax.get_ylim()
                        v = simpledialog.askfloat("Limit", f"{a.upper()} {s}:", initialvalue=curr[0] if s=='min' else curr[1])
                        if v is not None:
                            if a=='x': ax.set_xlim(left=v) if s=='min' else ax.set_xlim(right=v)
                            else: ax.set_ylim(bottom=v) if s=='min' else ax.set_ylim(top=v)
                            fig.canvas.draw_idle()
                    except Exception as e:
                        logger.exception("❌ Graph Interactor: Set limits failed")
                sl_menu.add_command(label="X Min", command=lambda: sl('x','min'))
                sl_menu.add_command(label="X Max", command=lambda: sl('x','max'))
                sl_menu.add_command(label="Y Min", command=lambda: sl('y','min'))
                sl_menu.add_command(label="Y Max", command=lambda: sl('y','max'))

                # --- SAVE ---
                sv_menu = tk.Menu(menu, tearoff=0); menu.add_cascade(label="Save Graph", menu=sv_menu)
                def _sv(p):
                    try:
                        was = annot.get_visible() if annot else False
                        if annot: annot.set_visible(False)
                        if hasattr(ax, "_hover_vline"): ax._hover_vline.set_visible(False)
                        for d in getattr(ax, "_hover_dots", []): d.set_visible(False)
                        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        w1 = fig.create_text(0.98, 0.04, "AIR", color="#33A1FD", fontsize=16, ha='right', va='bottom')
                        w2 = fig.create_text(0.935, 0.04, "OPEN", color="#FF6B35", fontsize=16, fontweight='bold', ha='right', va='bottom')
                        w3 = fig.create_text(0.98, 0.015, now, color="#888888", fontsize=10, ha='right', va='bottom')
                        fig.savefig(p, dpi=fig.dpi*4)
                        w1.remove(); w2.remove(); w3.remove()
                        if was: annot.set_visible(True)
                        fig.canvas.draw_idle()
                        if LOCAL_DEBUG: logger.success(f"✅ Graph saved to: {p}")
                    except Exception as e:
                        logger.exception("❌ Graph Interactor: Save failed")
                def qsv():
                    from workers.initialization.worker_project_paths import GLOBAL_PROJECT_ROOT
                    d = GLOBAL_PROJECT_ROOT / "DATA" / "GRAPHS"; d.mkdir(parents=True, exist_ok=True)
                    fn = f"{ax.get_title().replace(' ','_') or 'Graph'}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    _sv(str(d / fn))
                sv_menu.add_command(label="Save (Quick)", command=qsv)
                sv_menu.add_command(label="Save As...", command=lambda: (p := filedialog.asksaveasfilename(defaultextension=".png")) and _sv(p))

                # --- BOTTOM ---
                menu.add_separator()
                zp = getattr(ax, "zoom_pan", None)
                if zp:
                    def res(): 
                        try:
                            ax.set_xlim(zp.initial_xlim); ax.set_ylim(zp.initial_ylim); res_iso()
                        except Exception as e:
                            logger.exception("❌ Graph Interactor: View reset failed")
                    menu.add_command(label="Reset View", command=res)
                menu.add_command(label="Autoscale", command=lambda: (ax.relim(), ax.autoscale(enable=True, axis='both', tight=True), fig.canvas.draw_idle()))

                try: menu.post(event.guiEvent.x_root, event.guiEvent.y_root)
                except Exception as e:
                    logger.exception("❌ Graph Interactor: Menu post failed")
            except Exception as e:
                logger.exception("❌ Graph Interactor: Context menu crash")

        ax.hover_enabled = True
        if nav_config.get("enable_zoom") or nav_config.get("enable_pan"):
            ax.zoom_pan = ZoomPan(ax, callbacks, on_context_menu)
    except Exception as e:
        logger.exception("❌ Graph Interactor: Setup failed")
