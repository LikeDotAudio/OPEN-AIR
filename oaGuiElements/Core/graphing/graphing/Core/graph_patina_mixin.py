import numpy as np
from PIL import Image
from oaLogging.Core.logger import builder_logger
from oaGuiElements.Core.graphing.graphing import graph_updater

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True

class GraphPatinaMixin:
    """Injects high-fidelity patina textures from the parent GUI builder into the Matplotlib figure."""

    def _on_patina_update(self):
        # 🛡️ REBUILD GUARD
        if getattr(self.instance, '_is_rebuilding', False): return

        if BUILDER_DEBUG: builder_logger.debug(f"📈💹🎨 [SYNC] Injecting patina into FluxPlotter '{self.widget_id}'")
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
                
                visible = not (has_patina or is_trans)
                self.fig.patch.set_visible(visible)
                self.ax.patch.set_visible(visible)
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
