# Managers/gui_re.py
# Author: Anthony Peter Kuzub
# Version 20260330.1600.1
#
# Description: Handles the destruction and re-initialization of the GUI Frame.

from oaLogging.Methods.matrix_gate import matrix_log
from oaGui.Methods.gui_destruction_engine import GuiDestructionEngine
from oaGui.Methods.builder_path_resolver import BuilderPathResolver

class GuiRebuilderMixin:
    """Mixin for destroying and recreating the GUI content."""

    def _force_rebuild_gui(self):
        """Forces a complete rebuild by clearing the hash."""
        matrix_log("ui", "gui_re", "_force_rebuild_gui",
                   f"♻️ Rebuilder: FORCING GUI rebuild for '{getattr(self, 'tab_name', 'Unknown')}'", "INFO")

        from oaGui.Core.factory.asset_cache import AssetCacheManager
        from oaGui.FileReaders.blueprint_loader import BlueprintLoader
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

        from oaGui.Workers.transparency.transparency import TransparencyManager
        TransparencyManager.cleanup(self)

        # 1. Destruction pass
        destroyed_count = 0
        if hasattr(self, 'scroll_frame') and self.scroll_frame.winfo_exists():
            destroyed_count = GuiDestructionEngine.destroy_content(self.scroll_frame)

        matrix_log("ui", "gui_re", "_rebuild_gui", f"  └─ 💥 Destroyed {destroyed_count} widgets.", "TRACE")
        self.topic_widgets.clear()

        def on_build_complete():
            if not self.winfo_exists(): return
            matrix_log("ui", "gui_re", "on_build_complete",
                       f"♻️🆗✅ [RENDER] Rebuilder: Build sequence FINISHED for '{getattr(self, 'tab_name', 'Unknown')}'", "INFO")

            def _final_settle():
                if not self.winfo_exists(): return
                if hasattr(self, 'layout_manager') and getattr(self, 'canvas', None) is not None and self.canvas.winfo_exists():
                    self.layout_manager.perform_canvas_resize(self.canvas.winfo_width(), self.canvas.winfo_height())

                if hasattr(self, '_trigger_reslice_all'): self._trigger_reslice_all()
                if hasattr(self, '_publish_initial_widget_states'): self._publish_initial_widget_states(self.config_data)
                if hasattr(self, 'on_complete_callback') and self.on_complete_callback: self.on_complete_callback()

            def _wrap_settle():
                if not self.winfo_exists(): return
                _final_settle()
                self._is_rebuilding = False

            self.after(200, _wrap_settle)

        matrix_log("ui", "gui_re", "_rebuild_gui", "♻️ Rebuilder: Handing off to BatchBuilder for creation pass.", "DEBUG")

        # 2. Creation pass
        path_prefix = BuilderPathResolver.resolve_prefix(self.config_data)

        if hasattr(self, '_create_dynamic_widgets'):
            self._create_dynamic_widgets(
                self.scroll_frame,
                self.config_data,
                path_prefix=path_prefix,
                on_complete=on_build_complete
            )
        else:
            matrix_log("ui", "gui_re", "_rebuild_gui", f"❌ Rebuilder: Missing _create_dynamic_widgets in {self}", "ERROR")
            self._is_rebuilding = False
