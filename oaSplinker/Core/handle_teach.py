# Core/handle_teach.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

def handle_teach(self, topic):
    for s in self.splinks:
        if s["id"] == self.active_splink_id:
            s["dest"] = topic
            self.teaching_dest = False
            self.save_splink(s)
            break
