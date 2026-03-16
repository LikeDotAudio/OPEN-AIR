# core/gui_rebuilder.py
#
# Handles the destruction and re-initialization of the GUI Frame.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20250821.200641.1

import tkinter as tk
from loguru import logger
from managers.configini.config_reader import Config

LOCAL_DEBUG = True    # Set to False in production, True for dev on this file

app_constants = Config.get_instance()

class GuiRebuilderMixin:
    """Handles the destruction and re-initialization of the GUI Frame."""

    def _force_rebuild_gui(self):
        """Forces a complete rebuild by clearing the hash."""
        if LOCAL_DEBUG: logger.info(f"♻️ Rebuilder: FORCING GUI rebuild for '{getattr(self, 'tab_name', 'Unknown')}'")
        
        # ⚡ OPTIMIZATION: Clear the default config cache to allow editing default_panel.json
        from managers.Display.loader.blueprint_loader import BlueprintLoader
        from managers.Display.factory.asset_cache import AssetCacheManager
        BlueprintLoader.invalidate_cache()
        AssetCacheManager.invalidate_cache()

        self.last_build_hash = None
        self._load_and_build_from_file()

    def _rebuild_gui(self):
        """Rebuilds the GUI by destroying existing widgets and recreating them."""
        # ⚡ PRECONDITION VALIDATION
        if not self.winfo_exists():
            return

        if LOCAL_DEBUG: logger.debug(f"♻️ Rebuilder: Starting destruction of current UI for '{getattr(self, 'tab_name', 'Unknown')}'")
        
        # ⚡ OPTIMIZATION: Set rebuilding flag to suppress transient warnings
        self._is_rebuilding = True

        # ⚡ OPTIMIZATION: Use centralized cleanup to clear slicing registry and force GC
        from managers.Display.transparency.transparency import TransparencyManager
        TransparencyManager.cleanup(self)

        # Destroy all children in the scroll frame, EXCEPT the background label
        destroyed_count = 0
        if hasattr(self, 'scroll_frame') and self.scroll_frame.winfo_exists():
            for child in self.scroll_frame.winfo_children():
                if hasattr(self, 'panel_bg_label') and child == self.panel_bg_label:
                    continue
                child.destroy()
                destroyed_count += 1
        
        if LOCAL_DEBUG: logger.trace(f"  └─ 💥 Destroyed {destroyed_count} widgets.")

        self.topic_widgets.clear()
        self.update_idletasks()

        def on_build_complete():
            if not self.winfo_exists(): return
            if LOCAL_DEBUG: logger.debug(f"♻️ Rebuilder: Build sequence FINISHED for '{getattr(self, 'tab_name', 'Unknown')}'")
            
            # ⚡ MANDATORY: Update idle tasks and wait a brief moment for geometry managers to settle
            self.update_idletasks()

            def _final_settle():
                if not self.winfo_exists(): return
                # Force update of window size to match new content for proper scrolling
                self.update_idletasks()
                if hasattr(self, '_perform_canvas_resize') and hasattr(self, 'canvas') and self.canvas.winfo_exists():
                    self._perform_canvas_resize(self.canvas.winfo_width())
                
                # Trigger final reslice once all widgets are created and placed
                if hasattr(self, '_trigger_reslice_all'):
                    self._trigger_reslice_all()

                # Call the user-defined callback if it exists
                if hasattr(self, 'on_complete_callback') and self.on_complete_callback:
                    self.on_complete_callback()

            # 200ms delay to ensure the OS and Tkinter have finalized the window hierarchy
            def _wrap_settle():
                if not self.winfo_exists(): return
                _final_settle()
                self._is_rebuilding = False
            
            self.after(200, _wrap_settle)

        # Use the new async field processor
        if LOCAL_DEBUG: logger.debug(f"♻️ Rebuilder: Handing off to BatchBuilder for creation pass.")
        if hasattr(self, '_create_dynamic_widgets'):
            self._create_dynamic_widgets(self.scroll_frame, self.config_data, on_complete=on_build_complete)
        else:
            logger.error(f"❌ Rebuilder: Missing _create_dynamic_widgets in {self}")
            self._is_rebuilding = False

