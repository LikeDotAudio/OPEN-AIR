# oaGui/Managers/tabs/tab_editor_launcher.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Service for identifying and launching the WYSIWYG editor from a tab context.

def launch_tab_editor(tab_instance, tab_frame):
    """Traverses the widget hierarchy starting from a tab frame to find and invoke the editor."""
    queue = [tab_frame]
    
    while queue:
        current = queue.pop(0)
        
        # Check for direct editor capability
        if hasattr(current, "_show_wysiwyg_editor"):
            current._show_wysiwyg_editor()
            return
            
        # Check for nested dynamic GUI container
        if hasattr(current, "dynamic_gui"):
            if hasattr(current.dynamic_gui, "_show_wysiwyg_editor"):
                current.dynamic_gui._show_wysiwyg_editor()
                return
                
        # Descend into children
        for child in current.winfo_children():
            queue.append(child)
