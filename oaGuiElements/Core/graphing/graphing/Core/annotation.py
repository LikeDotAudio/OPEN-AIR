# Core/annotation.py
from oaGuiFramework.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import numpy as np

class AnnotationManager:
    """Handles hover-based annotations, intersection dots, and vertical crosshair lines."""

    @staticmethod
    def update(event, ax, annot):
        v_line = getattr(ax, "_hover_vline", None)
        dots = getattr(ax, "_hover_dots", [])

        if event.inaxes == ax and getattr(ax, "hover_enabled", True):
            data_text, marker_text, active_dot_count = [], [], 0
            if v_line: v_line.set_xdata([event.xdata, event.xdata]); v_line.set_visible(True)

            for line in ax.lines:
                if not line.get_visible() or line == v_line: continue
                label = line.get_label()
                if not label or label.startswith("_"): continue
                
                x_d, y_d = line.get_xdata(), line.get_ydata()
                if len(x_d) == 0: continue
                
                if "Marker" in label or "MRK" in label:
                    if np.all(x_d == x_d[0]): marker_text.append(f"{label}: X={x_d[0]:.2f}")
                    elif np.all(y_d == y_d[0]): marker_text.append(f"{label}: Y={y_d[0]:.2f}")
                    continue

                idx = (np.abs(np.array(x_d) - event.xdata)).argmin()
                val_x, val_y = x_d[idx], y_d[idx]
                data_text.append(f"{label}: {val_y:.2f}")

                if active_dot_count < len(dots):
                    dots[active_dot_count].set_data([val_x], [val_y])
                    dots[active_dot_count].set_color(line.get_color())
                    dots[active_dot_count].set_visible(True)
                    active_dot_count += 1
            
            for i in range(active_dot_count, len(dots)): dots[i].set_visible(False)

            if data_text or marker_text:
                content = [f"X: {event.xdata:.2f}"] + data_text + (["---"] if data_text and marker_text else []) + marker_text
                annot.set_text("\n".join(content)); annot.xy = (event.xdata, event.ydata); annot.set_visible(True)
                ax.figure.canvas.draw_idle()
        else:
            if annot.get_visible(): annot.set_visible(False)
            if v_line: v_line.set_visible(False)
            for d in dots: d.set_visible(False)
            ax.figure.canvas.draw_idle()