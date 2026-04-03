# Managers/gui_re.py
#
# Handles the destruction and re-initialization of the GUI Frame.
# Implements optimized cleanup and batched creation for high-speed updates.
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
from oaLogging.Methods.matrix_gate import is_debug_allowed, matrix_log

def _is_debug():
    return is_debug_allowed(system="UI", element="GUI_BUILDER")

from oaConfiguration.FileReaders.config_reader import Config

class GuiRebuilderMixin:
    """Mixin for destroying and recreating the GUI content."""

    def _force_rebuild_gui(self):
        """Forces a complete rebuild by clearing the hash."""
        matrix_log("ui", "gui_re", "_force_rebuild_gui", 
                   f"♻️ Rebuilder: FORCING GUI rebuild for '{getattr(self, 'tab_name', 'Unknown')}'", "INFO")
        
        from oaGuiManager.FileReaders.blueprint_loader import BlueprintLoader
        from oaGuiManager.Core.factory.asset_cache import AssetCacheManager
        BlueprintLoader.invalidate_cache()
        AssetCacheManager.invalidate_cache()

        self.last_build_hash = None
        self._load_and_build_from_file()

    def _rebuild_gui(self):
        """Rebuilds the GUI by destroying existing widgets and recreating them."""
        if not self.winfo_exists(): return

        matrix_log("ui", "gui_re", "_rebuild_gui", 
                   f"♻️ Rebuilder: Starting destruction of current UI for '{getattr(self, 'tab_name', 'Unknown')}'", "DEBUG")
        
        self._is_rebuilding = True

        from oaGuiManager.Core.transparency.transparency import TransparencyManager
        TransparencyManager.cleanup(self)

        destroyed_count = 0
        if hasattr(self, 'scroll_frame') and self.scroll_frame.winfo_exists():
            for child in self.scroll_frame.winfo_children():
                if hasattr(self, 'panel_bg_label') and child == self.panel_bg_label:
                    continue
                child.destroy()
                destroyed_count += 1
        
        matrix_log("ui", "gui_re", "_rebuild_gui", f"  └─ 💥 Destroyed {destroyed_count} widgets.", "TRACE")

        self.topic_widgets.clear()
        self.update_idletasks()

        def on_build_complete():
            if not self.winfo_exists(): return
            matrix_log("ui", "gui_re", "on_build_complete", 
                       f"♻️ Rebuilder: Build sequence FINISHED for '{getattr(self, 'tab_name', 'Unknown')}'", "DEBUG")
            
            self.update_idletasks()

            def _final_settle():
                if not self.winfo_exists(): return
                self.update_idletasks()
                if hasattr(self, '_perform_canvas_resize') and hasattr(self, 'canvas') and self.canvas.winfo_exists():
                    self._perform_canvas_resize(self.canvas.winfo_width())
                
                if hasattr(self, '_trigger_reslice_all'):
                    self._trigger_reslice_all()

                if hasattr(self, '_publish_initial_widget_states'):
                    self._publish_initial_widget_states(self.config_data)

                if hasattr(self, 'on_complete_callback') and self.on_complete_callback:
                    self.on_complete_callback()

            def _wrap_settle():
                if not self.winfo_exists(): return
                _final_settle()
                self._is_rebuilding = False
            
            self.after(200, _wrap_settle)

        matrix_log("ui", "gui_re", "_rebuild_gui", "♻️ Rebuilder: Handing off to BatchBuilder for creation pass.", "DEBUG")
        if hasattr(self, '_create_dynamic_widgets'):
            self._create_dynamic_widgets(self.scroll_frame, self.config_data, on_complete=on_build_complete)
        else:
            matrix_log("ui", "gui_re", "_rebuild_gui", f"❌ Rebuilder: Missing _create_dynamic_widgets in {self}", "ERROR")
            self._is_rebuilding = False
