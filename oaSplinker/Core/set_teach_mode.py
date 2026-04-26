# Core/set_teach_mode.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from ..Constants.constants import Splinker_debug_enabled, splinker_logger


def set_teach_mode(self, splink_id):
    self.active_splink_id = splink_id
    self.teaching_dest = True
    self.learning_source = False
    log_message = f"🔗 Splinker: TEACH mode active for {splink_id}"
    if Splinker_debug_enabled:
        splinker_logger.info(log_message)
        self._notify_monitor("debug_log", log_message)
