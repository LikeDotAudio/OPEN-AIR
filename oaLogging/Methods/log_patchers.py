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

    from oaLogging.Methods.config_retrieval import _get_cached_config

    config = _get_cached_config()
    if not config.global_settings.get("timestamp_logs", True):
        record["extra"]["ptp_time"] = "000000.000"
        return

    ptp_now = get_ptp_time()
    current_second = int(ptp_now)

    # Cache the HHMMSS string and only update when the integer second changes.
    if current_second != _last_ptp_second:
        dt = datetime.fromtimestamp(ptp_now)
        _cached_hhmmss = dt.strftime("%H%M%S")
        _last_ptp_second = current_second

    # Append milliseconds using fast f-string formatting.
    ms = int((ptp_now - current_second) * 1000)
    record["extra"]["ptp_time"] = f"{_cached_hhmmss}.{ms:03d}"

    # Ensure 'category' is always present to avoid KeyErrors in sinks that expect it.
    if "category" not in record["extra"]:
        record["extra"]["category"] = "UNSET"
