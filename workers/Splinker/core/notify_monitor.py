from ..constants import splinker_logger

def notify_monitor(self, msg_type, data):
    for cb in self._monitor_callbacks:
        try:
            cb(msg_type, data)
        except Exception as e:
            splinker_logger.error(f"Splinker monitor callback error: {e}")
