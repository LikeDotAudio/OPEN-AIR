# Core/delete_splink.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Deletes a splink from the registry and storage.

def delete_splink(self, splink_id):
    self.registry.delete_splink(splink_id)
    if splink_id in self.splink_states:
        del self.splink_states[splink_id]

    file_path = self.storage_path / f"{splink_id}.json"
    if file_path.exists():
        file_path.unlink()

    self.publish_splinks()
