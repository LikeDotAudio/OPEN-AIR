# Core/graph_context_menu.py
from oaGui.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from tkinter import simpledialog, filedialog
import datetime
from loguru import logger

class GraphContextMenu:
    """Encapsulates the complex right-click context menu for Matplotlib graphs."""

    @staticmethod
    def show(event, fig, ax, annot, callbacks):
        try:
            menu = tk.Menu(fig.canvas.get_tk_widget(), tearoff=0)
            
            # 1. Markers
            m_menu = tk.Menu(menu, tearoff=0); menu.add_cascade(label="Markers", menu=m_menu)
            def add_m(t):
                val = event.xdata if t=='x' else event.ydata
                if callbacks and "on_add_marker" in callbacks and val is not None: callbacks["on_add_marker"](t, val)
            m_menu.add_command(label="Add Vertical Marker (X)", command=lambda: add_m('x'))
            m_menu.add_command(label="Add Horizontal Marker (Y)", command=lambda: add_m('y'))

            # 2. Isolation
            i_menu = tk.Menu(menu, tearoff=0); menu.add_cascade(label="Isolate", menu=i_menu)
            def _refresh_leg():
                if ax.get_legend_handles_labels()[1]: ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
                elif ax.get_legend(): ax.get_legend().remove()
            def do_iso(target=None):
                for l in ax.lines:
                    lb = l.get_label()
                    if lb and (lb.startswith("Marker") or lb.startswith("MRK")): l.set_label("_nolegend_")
                    l.set_visible(l == target if target else True)
                _refresh_leg(); fig.canvas.draw_idle()
            i_menu.add_command(label="Reset Isolation (Show All)", command=do_iso)
            i_menu.add_separator()
            for l in ax.lines:
                lb = l.get_label()
                if lb and not lb.startswith("_") and "Marker" not in lb and "MRK" not in lb:
                    i_menu.add_command(label=lb, command=lambda line=l: do_iso(line))

            # 3. Show/Hide
            sh_menu = tk.Menu(menu, tearoff=0); menu.add_cascade(label="Show / Hide", menu=sh_menu)
            sh_menu.add_command(label="Toggle Legend", command=lambda: (ax.get_legend().remove() if ax.get_legend() else _refresh_leg(), fig.canvas.draw_idle()))
            sh_menu.add_command(label="Toggle Grid", command=lambda: (ax.grid(), fig.canvas.draw_idle()))
            def toggle_cursor():
                ax.hover_enabled = not getattr(ax, "hover_enabled", True)
                if not ax.hover_enabled:
                    annot.set_visible(False)
                    if hasattr(ax, "_hover_vline"): ax._hover_vline.set_visible(False)
                    for d in getattr(ax, "_hover_dots", []): d.set_visible(False)
                fig.canvas.draw_idle()
            sh_menu.add_command(label="Toggle Cursor", command=toggle_cursor)

            # 4. Limits & Rename
            rn_menu = tk.Menu(menu, tearoff=0); menu.add_cascade(label="Rename", menu=rn_menu)
            def _rename_attribute(attr):
                v = simpledialog.askstring("Rename", f"New {attr}:", initialvalue=getattr(ax, f"get_{attr}")())
                if v: getattr(ax, f"set_{attr}")(v); fig.canvas.draw_idle()
            rn_menu.add_command(label="Chart Title", command=lambda: _rename_attribute("title"))
            rn_menu.add_command(label="X-Axis Label", command=lambda: _rename_attribute("xlabel"))
            rn_menu.add_command(label="Y-Axis Label", command=lambda: _rename_attribute("ylabel"))

            # 5. Save
            sv_menu = tk.Menu(menu, tearoff=0); menu.add_cascade(label="Save Graph", menu=sv_menu)
            def _save_graph(p):
                was = annot.get_visible(); annot.set_visible(False)
                if hasattr(ax, "_hover_vline"): ax._hover_vline.set_visible(False)
                for d in getattr(ax, "_hover_dots", []): d.set_visible(False)
                fig.savefig(p, dpi=fig.dpi*4); annot.set_visible(was); fig.canvas.draw_idle()
            sv_menu.add_command(label="Save (Quick)", command=lambda: _save_graph(f"Graph_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"))
            sv_menu.add_command(label="Save As...", command=lambda: (p := filedialog.asksaveasfilename(defaultextension=".png")) and _save_graph(p))

            menu.add_separator()
            if hasattr(ax, "zoom_pan"): menu.add_command(label="Reset View", command=ax.zoom_pan.reset_view)
            menu.add_command(label="Autoscale", command=lambda: (ax.relim(), ax.autoscale(enable=True, axis='both', tight=True), fig.canvas.draw_idle()))

            menu.post(event.guiEvent.x_root, event.guiEvent.y_root)
        except Exception as e: logger.exception("❌ Context menu failed")