# Core/background.py
#
# Manages the generation and application of procedural patina backgrounds
# for the builder panel. Uses background threads for heavy image processing.
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
# Version 20260330.1600.1

import tkinter as tk

from PIL import ImageTk

from oaGuiElements.Core.utils.panels.panel_generator import PanelGenerator

# --- Standard Debug Logging Setup ---
from oaLogging.Methods.matrix_gate import matrix_log
from oaStyle.Core.style import DEFAULT_THEME, THEMES


class BuilderBackgroundManagerMixin:
    """
    Mixin for managing procedural patina backgrounds in the GUI.
    """

    def _clear_panel_background(self):
        """Removes the generated panel background and restores the theme default."""
        matrix_log("ui", "gui_builder", "_clear_panel_background",
                   f"🎨🧹✨ [BUILDER] Clearing panel background for '{getattr(self, 'tab_name', 'Unknown')}'", "TRACE")

        if hasattr(self, 'panel_bg_label') and self.panel_bg_label:
            try:
                self.panel_bg_label.destroy()
            except Exception as e:
                matrix_log("ui", "gui_builder", "_clear_panel_background",
                           f"🎨 Clean: Label already gone or failed to destroy: {e}", "TRACE")
            self.panel_bg_label = None

        self.panel_bg_image = None
        self.panel_bg_pil = None
        if hasattr(self, '_last_bg_size'): del self._last_bg_size

        if hasattr(self, 'scroll_frame'):
            colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
            self.scroll_frame.configure(bg=colors["bg"])
            self._trigger_reslice_all()

    def _apply_panel_background(self, panel_config, width=None, height=None):
        """Generates and applies a procedural patina panel via background thread."""
        import threading

        # ⚡ RENDER TIER BYPASS: Skip procedural generation in Fast/Ghost modes
        render_tier = getattr(self, '_render_tier', 'high_res')
        if render_tier in ['fast', 'ghost']:
            matrix_log("ui", "gui_builder", "_apply_panel_background",
                       f"🎨⚡✨ [RENDER] Skipping procedural background for Tier: {render_tier}", "DEBUG")
            self._clear_panel_background()
            return

        if panel_config == "none":
            self._clear_panel_background()
            return

        if width is None or height is None:
            if getattr(self, 'canvas', None) is not None:
                w = self.canvas.winfo_width()
                h = self.canvas.winfo_height()
                if w <= 1 or h <= 1:
                    matrix_log("ui", "gui_builder", "_apply_panel_background",
                               f"🎨📐🔳 [BUILDER] Skipping bg regen for '{getattr(self, 'tab_name', 'Unknown')}': Canvas not yet sized.", "TRACE")
                    return
                width, height = w, h
            else:
                return

        width = max(50, width)
        height = max(50, height)

        matrix_log("ui", "gui_render", "_apply_panel_background",
                   f"🎨🎨🎨 [RENDER] Spawning background generation thread for '{getattr(self, 'tab_name', 'Unknown')}' ({width}x{height})", "INFO")

        if not hasattr(self, "_bg_task_id"): self._bg_task_id = 0
        self._bg_task_id += 1
        current_task_id = self._bg_task_id

        def _bg_worker():
            try:
                panel_bg_pil = PanelGenerator.generate_procedural_panel(width, height, panel_config)

                if self.winfo_exists() and self._bg_task_id == current_task_id:
                    self.after(0, lambda: self._apply_generated_background(panel_bg_pil, width, height, current_task_id))
            except Exception as e:
                from oaLogging.Core.logger import BUILDER_LOGGER
                BUILDER_LOGGER.error(f"❌🚫🛑 [ERROR] failure in background panel generation for '{getattr(self, 'tab_name', 'Unknown')}': {e}")
                if self.winfo_exists() and self._bg_task_id == current_task_id:
                    self.after(0, self._trigger_reslice_all)

        threading.Thread(target=_bg_worker, daemon=True).start()

    def _apply_generated_background(self, panel_bg_pil, width, height, task_id=None):
        """Applies the background PIL image to the UI (Main Thread)."""
        if not panel_bg_pil or not self.winfo_exists():
            return

        if task_id is not None and hasattr(self, "_bg_task_id") and self._bg_task_id != task_id:
            matrix_log("ui", "gui_builder", "_apply_generated_background",
                       f"⚠️🗑️🌀 [BUILDER] Background Task {task_id} discarded (superseded by {self._bg_task_id})", "DEBUG")
            return

        matrix_log("ui", "gui_render", "_apply_generated_background",
                   f"🎨🆗✅ [RENDER] Background applied to '{getattr(self, 'tab_name', 'Unknown')}' ({width}x{height})", "SUCCESS")

        self.panel_bg_pil = panel_bg_pil
        self.panel_bg_image = ImageTk.PhotoImage(self.panel_bg_pil)

        if self.panel_bg_image and hasattr(self, 'scroll_frame') and getattr(self, 'canvas', None) is not None:
            try:
                base_rgb = self.panel_bg_pil.getpixel((width//2, height//2))
                base_hex = '#%02x%02x%02x' % base_rgb[:3]
                self.scroll_frame.configure(bg=base_hex)
                self.canvas.configure(bg=base_hex)
            except Exception as e:
                matrix_log("ui", "gui_builder", "_apply_generated_background",
                           f"⚠️ Could not extract base color from background: {e}", "WARNING")

            if isinstance(self.scroll_frame, tk.Canvas):
                self.scroll_frame.delete("panel_procedural_bg")
                self.scroll_frame.create_image(0, 0, image=self.panel_bg_image, anchor="nw", tags="panel_procedural_bg")
                self.scroll_frame.tag_lower("panel_procedural_bg")
            else:
                if not hasattr(self, 'panel_bg_label') or not self.panel_bg_label:
                    self.panel_bg_label = tk.Label(self.scroll_frame, image=self.panel_bg_image, bd=0)
                else:
                    self.panel_bg_label.config(image=self.panel_bg_image)

                # This prevents the canvas from being unnecessarily stretched by a large background image.
                req_w = self.scroll_frame.winfo_reqwidth()
                req_h = self.scroll_frame.winfo_reqheight()
                final_w = max(width, req_w)
                final_h = max(height, req_h)

                # ⚡ ROBUSTNESS: Prevent X11 BadValue (0x0) errors by avoiding place()
                # with zero dimensions.
                if final_w <= 1 or final_h <= 1:
                    matrix_log("gui", "gui_builder", "_apply_generated_background", f"🎨📐🔳 [BG] Skipping place for background label: Invalid dimensions {final_w}x{final_h}", "TRACE")
                    return

                matrix_log("gui", "gui_builder", "_apply_generated_background", 
                           f"🎨📏✨ [BG] Sizing background label to {final_w}x{final_h} | "
                           f"Source: {width}x{height} | Req: {req_w}x{req_h}", "TRACE")
                self.panel_bg_label.place(x=0, y=0, width=final_w, height=final_h)

                # ⚡ Z-STACK FIX: Force the background to the bottom and update the UI *before* reslicing
                self.panel_bg_label.lower()

            self._trigger_reslice_all(force=True)

    def _force_background_to_back(self):
        """Ensures the background label is at the bottom of the Z-stack."""
        if hasattr(self, 'panel_bg_label') and self.panel_bg_label:
            try:
                self.panel_bg_label.lower()
            except Exception:
                pass

    def _trigger_background_sync(self, force=False):
        """Calculates settled dimensions and triggers background regeneration."""
        if not self.winfo_exists(): return

        # ⚡ BYPASS: If force is True, we proceed even if rebuilding (critical for editor updates)
        if not force and getattr(self, '_is_rebuilding', False):
            matrix_log("ui", "gui_builder", "_trigger_background_sync",
                       f"🎨📐🔳 [LAYOUT] BG Sync BLOCKED for '{getattr(self, 'tab_name', 'Unknown')}': Rebuild in progress.", "TRACE")
            return

        if hasattr(self, '_bg_sync_timer') and self._bg_sync_timer:
            self.after_cancel(self._bg_sync_timer)

        if not force:
            self._bg_sync_timer = self.after(100, lambda: self._perform_background_sync(force=False))
        else:
            self._perform_background_sync(force=True)

    def _perform_background_sync(self, force=False):
        """Internal execution logic for background sync."""
        self._bg_sync_timer = None
        if not self.winfo_exists() or not self.winfo_ismapped():
            return

        if getattr(self, 'canvas', None) is None or not hasattr(self, 'scroll_frame'):
            return

        # 📏 DIMENSION CALCULATION
        # We fit the background to the ACTUAL size of the scroll_frame container.
        # The CanvasViewportManager is responsible for sizing this frame.
        w = self.scroll_frame.winfo_width()
        h = self.scroll_frame.winfo_height()
        
        # Fallback to requested size if not yet physically realized
        if w <= 1: w = self.scroll_frame.winfo_reqwidth()
        if h <= 1: h = self.scroll_frame.winfo_reqheight()

        matrix_log("gui", "gui_builder", "_perform_background_sync", 
                   f"🎨 [BG_SYNC] Tab: {getattr(self, 'tab_name', '??')} | "
                   f"Actual Frame Size: {w}x{h}", "TRACE")

        if w <= 1 or h <= 1: return

        last_w, last_h = getattr(self, '_last_bg_size', (0, 0))

        # ⚡ IMPROVED: Regenerate if size changed significantly
        needs_regen = force or abs(w - last_w) > 20 or abs(h - last_h) > 20

        if not needs_regen:
            self._trigger_reslice_all()
            return

        self._last_bg_size = (w, h)

        bg_config = getattr(self, 'config_data', {}).get("background")
        if bg_config and bg_config != "none":
            if isinstance(bg_config, dict):
                params = bg_config.get("parameters", bg_config)
                if "random_seed" not in params:
                    import random
                    params["random_seed"] = random.randint(1, 1000000)

                # ⚡ RESOLUTION INJECTION: Driven by _render_tier
                render_tier = getattr(self, '_render_tier', 'fast')
                if render_tier == 'high_res':
                    params["scale_factor"] = 2.0
                else:
                    params["scale_factor"] = 1.0

            self._apply_panel_background(bg_config, w, h)
        else:
            self._clear_panel_background()
            self._trigger_reslice_all()
