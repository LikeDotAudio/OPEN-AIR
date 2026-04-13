# Core/toggle_splink.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Toggles the active state of a splink.

def toggle_splink(self, splink_id):
    splink_instance = self.registry.get_splink_by_id(splink_id)
    if splink_instance:
        splink_instance["active"] = not splink_instance.get("active", False)
        self.registry.update_splink(splink_id, splink_instance)
        self._save_splink(splink_instance)
        self.publish_splinks()
