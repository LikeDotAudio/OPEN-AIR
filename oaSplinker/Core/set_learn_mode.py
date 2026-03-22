# Core/set_learn_mode.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from ..Constants.constants import Splinker_debug_enabled, splinker_logger

def set_learn_mode(self, splink_id):
    self.active_splink_id = splink_id
    self.learning_source = True
    self.teaching_dest = False
    log_msg = f"🔗 Splinker: LEARN mode active for {splink_id}"
    if Splinker_debug_enabled:
        splinker_logger.info(log_msg)
        self._notify_monitor("debug_log", log_msg)
