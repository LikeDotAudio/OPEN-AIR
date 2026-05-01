# Methods/gui_destruction_engine.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Handles optimized destruction of Tkinter widget trees.

from oaLogging.Methods.matrix_gate import matrix_log

class GuiDestructionEngine:
    """Handles optimized destruction of Tkinter widget trees."""
    @staticmethod
    def destroy_content(container, preserve_tags=None):
        """Rebuilds the GUI by destroying existing widgets and recreating them."""
        if not container.winfo_exists(): return 0

        destroyed_count = 0
        for child in container.winfo_children():
            # Check if we should preserve this specific child
            if preserve_tags and hasattr(child, 'tags') and any(tag in preserve_tags for tag in child.tags):
                 continue
            
            # ⚡ SPECIAL CASE: Don't destroy the background patina label if it's managed externally
            if hasattr(container, 'panel_bg_label') and child == container.panel_bg_label:
                continue

            child.destroy()
            destroyed_count += 1
        
        return destroyed_count
