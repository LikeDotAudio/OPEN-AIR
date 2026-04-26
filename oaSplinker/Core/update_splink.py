# Core/update_splink.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from ..Constants.constants import Splinker_debug_enabled, splinker_logger


def update_splink(self, splink_id, new_data):
    """Updates an existing splink with new configuration."""
    for i, s in enumerate(self.splinks):
        if s["id"] == splink_id:
            self.splinks[i].update(new_data)
            self.save_splink(self.splinks[i])
            log_message = f"🔗 Splinker: Splink {splink_id} Updated."
            if Splinker_debug_enabled:
                splinker_logger.info(log_message)
                self.notify_monitor("debug_log", log_message)
            return
