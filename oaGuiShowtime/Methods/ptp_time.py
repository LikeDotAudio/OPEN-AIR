# Methods/ptp_time.py
# Author: Anthony Peter Kuzub
# Version: 20260222.Optimized.1
#
# Description: Provides Precision Time Protocol (PTP) synchronized time using CLOCK_TAI.

import time
from datetime import datetime

# ⚡ CLOCK DISCOVERY: Perform once at module load
_CLOCK_FUNC = time.time
_IS_PTP = False

if hasattr(time, 'CLOCK_TAI'):
    try:
        # Test if the clock is actually accessible
        time.clock_gettime(time.CLOCK_TAI)
        _CLOCK_FUNC = lambda: time.clock_gettime(time.CLOCK_TAI)
        _IS_PTP = True
    except (OSError, AttributeError):
        pass

def get_ptp_time():
    """
    Retrieves the current PTP (TAI) time if available.
    Zero-overhead: uses the pre-discovered best available clock function.
    """
    return _CLOCK_FUNC()

def is_using_ptp():
    """Returns True if the system is currently using CLOCK_TAI."""
    return _IS_PTP

def get_ptp_timestamp_str(format_str="%H:%M:%S.%f"):
    """
    Returns a formatted string of the current PTP time.
    Useful for logging and UI displays.
    """
    ptp_now = get_ptp_time()
    dt = datetime.fromtimestamp(ptp_now)
    # Truncate microseconds to 3 digits for cleaner logging
    return dt.strftime(format_str)[:-3]
