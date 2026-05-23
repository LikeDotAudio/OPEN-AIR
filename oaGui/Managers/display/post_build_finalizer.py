# oaGui/Managers/display/post_build_finalizer.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Handles post-build settlement and state initialization.

from oaLogging.Methods.matrix_gate import matrix_log


def finalize_gui_settlement(display_instance):
    """Coordinates the final positioning and state initialization after construction."""
    matrix_log("ui", "gui_builder", "finalize", "✅🏗️ [BUILDER] Finalizing GUI settlement...", "INFO")

    def _trigger_builders_refresh():
        for loader in display_instance.loader_facade.get_all_builders():
            if hasattr(loader, 'dynamic_gui') and loader.dynamic_gui.winfo_exists():
                builder = loader.dynamic_gui
                builder._trigger_reslice_all(force=True)
                builder._trigger_background_sync(force=True)

    # 1. Physical Sizing Settle
    display_instance.after(500, _trigger_builders_refresh)

    # 2. Functional Initialization
    display_instance.after(750, display_instance._trigger_initial_tab_selection)

    if display_instance.state_cache_manager:
        display_instance.after(1250, display_instance.state_cache_manager.initialize_state)

    # 3. Persistence
    display_instance.after(2250, lambda: display_instance.cache_manager.save(display_instance._layout_cache))

    if display_instance.on_complete_callback:
        display_instance.on_complete_callback()
