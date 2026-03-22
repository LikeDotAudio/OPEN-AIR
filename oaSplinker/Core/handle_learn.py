# Core/handle_learn.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

def handle_learn(self, topic):
    for s in self.splinks:
        if s["id"] == self.active_splink_id:
            s["source"] = topic
            self.learning_source = False
            self.save_splink(s)
            break
