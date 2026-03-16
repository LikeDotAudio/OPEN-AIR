from ..constants import Splinker_debug_enabled, splinker_logger

def _update_splink(self, splink_id, new_data):
    """Updates an existing splink with new configuration."""
    for i, s in enumerate(self.splinks):
        if s["id"] == splink_id:
            self.splinks[i].update(new_data)
            self._save_splink(self.splinks[i])
            log_msg = f"🔗 Splinker: Splink {splink_id} Updated."
            if Splinker_debug_enabled:
                splinker_logger.info(log_msg)
                self._notify_monitor("debug_log", log_msg)
            return
