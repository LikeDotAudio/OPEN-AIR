def toggle_splink(self, splink_id):
    for s in self.splinks:
        if s["id"] == splink_id:
            s["active"] = not s["active"]
            self._save_splink(s)
            break
