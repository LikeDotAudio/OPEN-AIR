# oaLogging/Methods/log_patchers.py
# Author: Gemini (Collaborator)
# Version: 20260413.1000.1
#
# Description: Log record patchers for high-precision timestamping.

import time
from datetime import datetime

try:
    from oaGuiShowtime.Methods.ptp_time import get_ptp_time
except ImportError:
    # Fallback for when ptp_time might not be available during early init
    def get_ptp_time():
        return time.time()

# --- Internal State for PTP Patcher ---
_last_ptp_second = -1
_cached_hhmmss = ""

def ptp_patcher(record):
    """
    Instruments log records with high-precision PTP (TAI) timestamps.
    Respects the global 'timestamp_logs' setting.
    """
    global _last_ptp_second, _cached_hhmmss

    # 1. Architectural Safety: Ensure required metadata exists for sinks
    if "category" not in record["extra"]:
        from oaLogging.Constants.subsystem_emojis import SUBSYSTEM_EMOJIS
        record["extra"]["category"] = SUBSYSTEM_EMOJIS.get("SYSTEM", "❓")
    
    if "category_name" not in record["extra"]:
        record["extra"]["category_name"] = "SYSTEM"

    from oaLogging.Methods.config_retrieval import _get_cached_config

    config = _get_cached_config()
    if not config.global_settings.get("timestamp_logs", True):
        record["extra"]["ptp_time"] = "000000.000"
        return
