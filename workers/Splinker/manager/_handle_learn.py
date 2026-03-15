def _handle_learn(self, topic):
    for s in self.splinks:
        if s["id"] == self.active_splink_id:
            s["source"] = topic
            self.learning_source = False
            self._save_splink(s)
            break
