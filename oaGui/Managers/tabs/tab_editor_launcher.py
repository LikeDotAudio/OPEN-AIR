# oaGui/Managers/tabs/tab_editor_launcher.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Service for identifying and launching the WYSIWYG editor from a tab context.

def find_tab_orchestrator(tab_frame):
    """Traverses the widget hierarchy starting from a tab frame to find a LoaderOrchestrator instance."""
    queue = [tab_frame]
    
    while queue:
        current = queue.pop(0)
        
        # Check if this widget itself is an orchestrator or has the direct editor capability
        if hasattr(current, "_show_wysiwyg_editor"):
            return current
            
        # Check for nested dynamic GUI container
        if hasattr(current, "dynamic_gui"):
            if hasattr(current.dynamic_gui, "_show_wysiwyg_editor"):
                return current.dynamic_gui
                
        # Descend into children
        for child in current.winfo_children():
            queue.append(child)
    return None
