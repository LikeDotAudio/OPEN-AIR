# Core/navigation.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import pathlib

class NavigationManagerMixin:
    """
    Handles specialized navigation between UI sections (e.g. jumping to Splinker).
    """

    def show_splinker_tab(self, src_topic=None, dest_topic=None):
        """
        Navigates to the Splinker tab and optionally populates it with topics.
        """
        target_path = pathlib.Path(self.app_constants.GLOBAL_PROJECT_ROOT) / "oaGuiDefinitions/right_50/bottom_90/4_Splinker"
        target_frame = self._frames_by_path.get(target_path)
        
        if not target_frame:
            target_frame = self._frames_by_path.get(pathlib.Path("oaGuiDefinitions/right_50/bottom_90/4_Splinker"))
            
        if target_frame:
            notebook = target_frame.master
            if hasattr(notebook, 'select'):
                notebook.select(target_frame)
                
                if src_topic or dest_topic:
                    def _update_dashboard():
                        if not getattr(target_frame, "is_populated", False):
                            self.after(100, _update_dashboard)
                            return
                            
                        for child in target_frame.winfo_children():
                            queue = [child]
                            while queue:
                                curr = queue.pop(0)
                                if hasattr(curr, 'set_pending_topics') and callable(getattr(curr, 'set_pending_topics')):
                                    curr.set_pending_topics(src_topic, dest_topic)
                                    return
                                for sub in curr.winfo_children():
                                    queue.append(sub)
                    
                    self.after(50, _update_dashboard)
