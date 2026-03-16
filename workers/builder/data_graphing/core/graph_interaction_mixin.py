import tkinter as tk
from tkinter import simpledialog
from loguru import logger

class GraphInteractionMixin:
    """Handles Matplotlib-specific interactions (Markers, Dragging, Renaming)."""

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
            if hasattr(self.dragging_marker, 'get_xdata'):
                xd, yd = self.dragging_marker.get_xdata(), self.dragging_marker.get_ydata()
                if len(xd) == 2 and xd[0] == xd[1] and e.xdata is not None: self.dragging_marker.set_xdata([e.xdata, e.xdata])
                elif len(yd) == 2 and yd[0] == yd[1] and e.ydata is not None: self.dragging_marker.set_ydata([e.ydata, e.ydata])
            self.canvas.draw_idle(); return
        
        hit = next((m for m in self.marker_objects if m.contains(e)[0]), None)
        if hit:
            if self.highlighted_marker != hit:
                if self.highlighted_marker: self._restore_marker_style(self.highlighted_marker)
                self.highlighted_marker = hit; self._save_marker_style(hit); self._apply_highlight(hit); self.canvas.draw_idle()
        elif self.highlighted_marker:
            self._restore_marker_style(self.highlighted_marker); self.highlighted_marker = None; self.canvas.draw_idle()

    def _on_marker_release(self, e):
        if self.dragging_marker:
            lbl = self.dragging_marker.get_label()
            if hasattr(self.dragging_marker, 'get_xdata'):
                xd, yd = self.dragging_marker.get_xdata(), self.dragging_marker.get_ydata()
                if len(xd) == 2 and xd[0] == xd[1]: self._update_marker_value(lbl, xd[0])
                elif len(yd) == 2 and yd[0] == yd[1]: self._update_marker_value(lbl, yd[0])
            self.dragging_marker = None

    def _save_marker_style(self, m):
        self.saved_style = {}
        if hasattr(m, 'get_color'): self.saved_style['color'] = m.get_color()
        if hasattr(m, 'get_linewidth'): self.saved_style['linewidth'] = m.get_linewidth()

    def _restore_marker_style(self, m):
        if not getattr(self, 'saved_style', None): return
        try:
            if 'color' in self.saved_style: m.set_color(self.saved_style['color'])
            if 'linewidth' in self.saved_style: m.set_linewidth(self.saved_style['linewidth'])
        except Exception as e:
            logger.trace(f"Error restoring marker style: {e}")
        self.saved_style = {}

    def _apply_highlight(self, m):
        try:
            m.set_color('yellow')
            if hasattr(m, 'set_linewidth'): m.set_linewidth(m.get_linewidth() + 2)
        except Exception as e:
            logger.trace(f"Error applying marker highlight: {e}")
