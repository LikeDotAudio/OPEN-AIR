# Core/graph_patina_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import numpy as np
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
from PIL import Image
from oaLogging.Core.logger import builder_logger
from oaGuiElements.Core.graphing.graphing import graph_updater

# --- Standard Debug Logging Setup ---
from oaLogging.Methods.matrix_gate import is_debug_allowed
BUILDER_DEBUG = is_debug_allowed(system="UI", element="GUI_BUILDER")

# --- Standard Debug Logging Setup ---

class GraphPatinaMixin:
    """Injects high-fidelity patina textures from the parent GUI builder into the Matplotlib figure."""

    def _on_patina_update(self):
        # 🛡️ REBUILD GUARD
        if getattr(self.instance, '_is_rebuilding', False): return

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📈💹🎨 [SYNC] Injecting patina into FluxPlotter '{self.widget_id}'", level="DEBUG")
        tk_canvas = self.canvas.get_tk_widget()
        
        # 0. Clear Blit Cache
        fig_id = id(self.fig)
        if fig_id in graph_updater._bg_cache: del graph_updater._bg_cache[fig_id]

        # 1. Sync flat color fallback
        try:
            bg_hex = tk_canvas.cget("bg")
            if bg_hex:
                has_patina = hasattr(tk_canvas, 'panel_bg_pil_slice')
                self.fig.patch.set_facecolor(bg_hex)
                self.ax.set_facecolor(bg_hex)
                
                is_trans = self.widget_config.get("transparent") is True or \
                           self.widget_config.get("style", {}).get("background_color") == "match_theme"
                
                # ⚡ FIX: Never hide the figure/axis patch if we want to see anything.
                # Matplotlib needs these to be visible to correctly capture the 'background' for blitting.
                # Instead of hiding them, we set their alpha or keep them as fallback.
                self.fig.patch.set_visible(True)
                self.ax.patch.set_visible(True)
                
                if has_patina or is_trans:
                    self.fig.patch.set_alpha(0.0)
                    self.ax.patch.set_alpha(0.0)
                else:
                    self.fig.patch.set_alpha(1.0)
                    self.ax.patch.set_alpha(1.0)
        except: pass

        # 2. Sync texture details
        if hasattr(tk_canvas, 'panel_bg_pil_slice'):
            try:
                slice_pil = tk_canvas.panel_bg_pil_slice
                w_px, h_px = self.canvas.get_width_height()
                if w_px > 1 and h_px > 1:
                    resized = slice_pil.resize((w_px, h_px), Image.Resampling.LANCZOS)
                    self.fig.images.clear()
                    self.fig.figimage(np.array(resized), 0, 0, zorder=-100, origin='upper')
                    self.fig.patch.set_visible(False)
                    self.ax.patch.set_visible(False)
            except Exception as e:
                if BUILDER_DEBUG: builder_logger.error(f"❌ FluxPlotter patina failed: {e}")

        # 3. Redraw
        self._force_redraw = True; self._schedule_update()
