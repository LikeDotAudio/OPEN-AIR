def delete_splink(self, splink_id):
    self.splinks = [s for s in self.splinks if s["id"] != splink_id]
    if splink_id in self.splink_states:
        del self.splink_states[splink_id]
    file_path = self.storage_path / f"{splink_id}.json"
    if file_path.exists():
        file_path.unlink()
    self._publish_splinks()
