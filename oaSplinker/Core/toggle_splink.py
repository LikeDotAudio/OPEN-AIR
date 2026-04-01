# Core/toggle_splink.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Toggles the active state of a splink.

def toggle_splink(self, splink_id):
    s = self.registry.get_splink_by_id(splink_id)
    if s:
        s["active"] = not s.get("active", False)
        self.registry.update_splink(splink_id, s)
        self._save_splink(s)
        self.publish_splinks()
