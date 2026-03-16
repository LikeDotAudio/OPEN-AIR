def handle_teach(self, topic):
    for s in self.splinks:
        if s["id"] == self.active_splink_id:
            s["dest"] = topic
            self.teaching_dest = False
            self.save_splink(s)
            break
