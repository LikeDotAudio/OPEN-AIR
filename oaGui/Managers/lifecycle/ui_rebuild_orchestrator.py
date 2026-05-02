# oaGui/Managers/lifecycle/ui_rebuild_orchestrator.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Orchestrates the destruction and recreation sequence for the GUI content.

from oaLogging.Methods.matrix_gate import matrix_log
from oaGui.Methods.execution.engine_destruction_service import GuiDestructionEngine
from oaGui.Methods.discovery.folder_path_resolver import BuilderPathResolver
from oaGui.Workers.compositing.engine_visual_effects import EngineVisualEffects

def orchestrate_ui_rebuild(lifecycle_instance):
    """Executes the high-fidelity UI reconstruction pipeline."""
    if not lifecycle_instance.winfo_exists():
        return

    tab_name = getattr(lifecycle_instance, 'tab_name', 'Unknown')
    matrix_log("ui", "lifecycle", "rebuild", f"♻️ Starting UI reconstruction for '{tab_name}'", "DEBUG")

    lifecycle_instance._is_rebuilding = True
    EngineVisualEffects.cleanup(lifecycle_instance)

    # 1. Physical Destruction
    count = 0
    if hasattr(lifecycle_instance, 'scroll_frame') and lifecycle_instance.scroll_frame.winfo_exists():
        count = GuiDestructionEngine.destroy_content(lifecycle_instance.scroll_frame)

    matrix_log("ui", "lifecycle", "rebuild", f"  └─ 💥 Liberated {count} widget resources.", "TRACE")
    lifecycle_instance.topic_widgets.clear()

    # 2. Re-Assembly
    prefix = BuilderPathResolver.resolve_prefix(lifecycle_instance.configuration)

    def _on_assembly_complete():
        _finalize_rebuild_sequence(lifecycle_instance, tab_name)

    if hasattr(lifecycle_instance, '_create_dynamic_widgets'):
        lifecycle_instance._create_dynamic_widgets(
            lifecycle_instance.scroll_frame,
            lifecycle_instance.configuration,
            path_prefix=prefix,
            on_complete=_on_assembly_complete
        )
    else:
        matrix_log("ui", "lifecycle", "rebuild", "❌ Rebuild failed: Assembler missing.", "ERROR")
        lifecycle_instance._is_rebuilding = False

def _finalize_rebuild_sequence(lifecycle_instance, tab_name):
    """Handles settling and state restoration after reconstruction."""
    if not lifecycle_instance.winfo_exists(): return
    
    matrix_log("ui", "lifecycle", "rebuild", f"✅ Build sequence complete for '{tab_name}'", "INFO")

    def _settle():
        if not lifecycle_instance.winfo_exists(): return
        
        # Geometry sync
        if hasattr(lifecycle_instance, 'layout_manager') and \
           getattr(lifecycle_instance, 'canvas', None) and \
           lifecycle_instance.canvas.winfo_exists():
            lifecycle_instance.layout_manager.perform_canvas_resize(
                lifecycle_instance.canvas.winfo_width(), 
                lifecycle_instance.canvas.winfo_height()
            )

        if hasattr(lifecycle_instance, '_trigger_reslice_all'): 
            lifecycle_instance._trigger_reslice_all()
            
        if hasattr(lifecycle_instance, '_publish_initial_widget_states'): 
            lifecycle_instance._publish_initial_widget_states(lifecycle_instance.configuration)
            
        if hasattr(lifecycle_instance, 'on_complete_callback') and \
           lifecycle_instance.on_complete_callback: 
            lifecycle_instance.on_complete_callback()
            
        lifecycle_instance._is_rebuilding = False

    lifecycle_instance.after(200, _settle)
