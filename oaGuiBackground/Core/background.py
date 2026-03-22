# Core/background.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import os
import time
import tkinter as tk
from tkinter import ttk
from PIL import ImageTk

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import builder_logger

from oaStyle.Core.style import DEFAULT_THEME, THEMES
from oaGuiElements.Core.utils.panels.panel_generator import PanelGenerator

class BuilderBackgroundManagerMixin:
    """
    Manages the generation and application of procedural patina backgrounds for the builder panel.
    """
    
    def _clear_panel_background(self):
        """Removes the generated panel background and restores the theme default."""
        if LOCAL_DEBUG: builder_logger.trace(f"🎨🧹✨ [BUILDER] Clearing panel background for '{getattr(self, 'tab_name', 'Unknown')}'")
        if hasattr(self, 'panel_bg_label') and self.panel_bg_label:
            try: self.panel_bg_label.destroy()
            except: pass
            self.panel_bg_label = None
        
        self.panel_bg_image = None
        self.panel_bg_pil = None
        if hasattr(self, '_last_bg_size'): del self._last_bg_size
        
        # Restore default background color
        if hasattr(self, 'scroll_frame'):
            colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
            self.scroll_frame.configure(bg=colors["bg"])
            self._trigger_reslice_all()

    def _apply_panel_background(self, panel_config, width=None, height=None):
        """
        Generates and applies a procedural patina panel to the whole tab.
        Moves heavy PIL generation to a background thread.
        """
        import threading
        
        # ⚡ ROBUSTNESS: Handle 'none' explicitly
        if panel_config == "none":
            self._clear_panel_background()
            return
        
        # ⚡ OPTIMIZATION: Prevent 'Guess' backgrounds during build.
        if width is None or height is None:
            if hasattr(self, 'canvas'):
                w = self.canvas.winfo_width()
                h = self.canvas.winfo_height()
                if w <= 1 or h <= 1:
                    if LOCAL_DEBUG: builder_logger.trace(f"🎨📐🔳 [BUILDER] Skipping bg regen for '{getattr(self, 'tab_name', 'Unknown')}': Canvas not yet sized.")
                    return
                width, height = w, h
            else:
                return
            
        # ⚡ FINAL SAFETY: Never request 0x0 or negative
        width = max(50, width)
        height = max(50, height)

        if LOCAL_DEBUG: builder_logger.info(f"🎨🏗️🌀 [BUILDER] Spawning background generation thread for '{getattr(self, 'tab_name', 'Unknown')}' ({width}x{height})")

        # ⚡ RACE CONDITION PROTECTION: Track the latest task ID
        if not hasattr(self, "_bg_task_id"): self._bg_task_id = 0
        self._bg_task_id += 1
        current_task_id = self._bg_task_id

        def _bg_worker():
            try:
                # 1. Generate (or Load from Cache) in background
                panel_bg_pil = PanelGenerator.generate_procedural_panel(width, height, panel_config)
                
                # 2. Schedule UI update on main thread (only if this is still the active task)
                if self.winfo_exists() and self._bg_task_id == current_task_id:
                    self.after(0, lambda: self._apply_generated_background(panel_bg_pil, width, height, current_task_id))
            except Exception as e:
                if LOCAL_DEBUG: builder_logger.exception(f"❌🚫🛑 [ERROR] failure in background panel generation for '{getattr(self, 'tab_name', 'Unknown')}'")
                # ⚡ FALLBACK: Trigger reslice anyway so widgets can update their theme-matched colors
                if self.winfo_exists() and self._bg_task_id == current_task_id:
                    self.after(0, self._trigger_reslice_all)

        threading.Thread(target=_bg_worker, daemon=True).start()

    def _apply_generated_background(self, panel_bg_pil, width, height, task_id=None):
        """Applies the background PIL image to the UI (Main Thread)."""
        if not panel_bg_pil or not self.winfo_exists():
            return

        # ⚡ RACE CONDITION PROTECTION: Verify task ID still matches
        if task_id is not None and hasattr(self, "_bg_task_id") and self._bg_task_id != task_id:
            if LOCAL_DEBUG: builder_logger.debug(f"⚠️🗑️🌀 [BUILDER] Background Task {task_id} discarded (superseded by {self._bg_task_id})")
            return

        if LOCAL_DEBUG: builder_logger.success(f"🎨🆗✨ [BUILDER] Applying generated background ({width}x{height}) to '{getattr(self, 'tab_name', 'Unknown')}' UI.")
        self.panel_bg_pil = panel_bg_pil
        self.panel_bg_image = ImageTk.PhotoImage(self.panel_bg_pil)
        
        if self.panel_bg_image and hasattr(self, 'scroll_frame') and hasattr(self, 'canvas'):
            # Extract base color from PIL (center pixel) for fallback
            try:
                base_rgb = self.panel_bg_pil.getpixel((width//2, height//2))
                base_hex = '#%02x%02x%02x' % base_rgb[:3]
                self.scroll_frame.configure(bg=base_hex)
                # ⚡ MANDATORY: Update canvas background too to avoid borders
                self.canvas.configure(bg=base_hex)
            except Exception as e:
                if LOCAL_DEBUG: builder_logger.warning(f"⚠️ Could not extract base color from background: {e}")
                pass

            # ⚡ CRITICAL FIX: If scroll_frame is a canvas, draw the image directly on it.
            # This is much more robust for Z-ordering than a Label with place().
            if isinstance(self.scroll_frame, tk.Canvas):
                self.scroll_frame.delete("panel_procedural_bg")
                self.scroll_frame.create_image(0, 0, image=self.panel_bg_image, anchor="nw", tags="panel_procedural_bg")
                self.scroll_frame.tag_lower("panel_procedural_bg")
            else:
                # Fallback for non-canvas scroll frames
                if not hasattr(self, 'panel_bg_label') or not self.panel_bg_label:
                    self.panel_bg_label = tk.Label(self.scroll_frame, image=self.panel_bg_image, bd=0)
                    self.panel_bg_label.place(x=0, y=0, width=width, height=height)
                    self.panel_bg_label.lower()
                else:
                    self.panel_bg_label.config(image=self.panel_bg_image)
                    self.panel_bg_label.place(x=0, y=0, width=width, height=height)
            
            # --- Trigger reslice for all registered widgets ---
            self._trigger_reslice_all()

    def _trigger_background_sync(self, force=False):
        """Calculates settled dimensions and triggers background regeneration with debouncing."""
        if not self.winfo_exists(): return
        
        # 🛡️ LOCK: Never trigger during the rebuild or mapping phase, unless FORCED.
        if not force and getattr(self, '_is_rebuilding', False):
            if LOCAL_DEBUG: builder_logger.trace(f"🎨📐🔳 [LAYOUT] BG Sync BLOCKED for '{getattr(self, 'tab_name', 'Unknown')}': Rebuild in progress.")
            return

        # ⚡ DEBOUNCE: Prevent rapid-fire syncs from triggering multiple threads
        if hasattr(self, '_bg_sync_timer') and self._bg_sync_timer:
            self.after_cancel(self._bg_sync_timer)
        
        if not force:
            self._bg_sync_timer = self.after(100, lambda: self._perform_background_sync(force=False))
        else:
            self._perform_background_sync(force=True)

    def _perform_background_sync(self, force=False):
        """Internal execution logic for background sync."""
        self._bg_sync_timer = None
        if not self.winfo_exists(): return
        
        if not self.winfo_ismapped():
            return
            
        if not hasattr(self, 'canvas') or not hasattr(self, 'scroll_frame'):
            return

        canv_w = self.canvas.winfo_width()
        canv_h = self.canvas.winfo_height()
        req_w = self.scroll_frame.winfo_reqwidth()
        req_h = self.scroll_frame.winfo_reqheight()
        
        w = max(canv_w, req_w)
        h = max(canv_h, req_h)
        
        if w <= 1 or h <= 1: return
        
        last_w, last_h = getattr(self, '_last_bg_size', (0, 0))
        
        needs_regen = False
        if force:
            needs_regen = True
        elif w > last_w or h > last_h:
            dw = max(0, w - last_w)
            dh = max(0, h - last_h)
            if dw > 50 or dh > 50:
                needs_regen = True
        
        if not needs_regen:
            self._trigger_reslice_all()
            return

        self._last_bg_size = (w, h)
        
        if hasattr(self, 'canvas_window_id') and self.canvas_window_id:
            self.canvas.itemconfig(self.canvas_window_id, width=w, height=h)

        bg_config = getattr(self, 'config_data', {}).get("background")
        if bg_config and bg_config != "none":
            if isinstance(bg_config, dict):
                params = bg_config.get("parameters", bg_config)
                if "random_seed" not in params:
                    import random
                    params["random_seed"] = random.randint(1, 1000000)
            self._apply_panel_background(bg_config, w, h)
        else:
            self._clear_panel_background()
            self._trigger_reslice_all()
