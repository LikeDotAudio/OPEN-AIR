# oaGui/Managers/tabs/tab_editor_launcher.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Service for identifying and launching the WYSIWYG editor from a tab context.

from oaLogging.Methods.matrix_gate import matrix_log

def find_tab_orchestrator(tab_frame):
    """Traverses the widget hierarchy starting from a tab frame to find a LoaderOrchestrator instance."""
    queue = [tab_frame]
    
    matrix_log("gui", "gui_shell", "find_tab_orchestrator", f"🔍 Starting search in tab frame: {tab_frame}", "DEBUG")

    while queue:
        current = queue.pop(0)
        
        # Check if this widget itself is an orchestrator or has the direct editor capability
        if hasattr(current, "_show_wysiwyg_editor"):
            matrix_log("gui", "gui_shell", "find_tab_orchestrator", f"✅ Found orchestrator directly: {current}", "DEBUG")
            return current
            
        # Check for nested dynamic GUI container
        if hasattr(current, "dynamic_gui"):
            if hasattr(current.dynamic_gui, "_show_wysiwyg_editor"):
                matrix_log("gui", "gui_shell", "find_tab_orchestrator", f"✅ Found orchestrator in dynamic_gui: {current.dynamic_gui}", "DEBUG")
                return current.dynamic_gui
                
        # Descend into children
        for child in current.winfo_children():
            queue.append(child)
    
    matrix_log("gui", "gui_shell", "find_tab_orchestrator", f"❌ No orchestrator found in {tab_frame} hierarchy.", "WARNING")
    return None
