# oaPTP/Methods/__init__.py
# Author: Anthony Peter Kuzub
# Version: 20260331.2140.1

import logging

try:
    from .ptp_clock import PtpClock
except Exception as e:
    logging.error(f"❌ [PTP] Failed to import PtpClock from .ptp_clock: {e}")
    class PtpClock:
        def __init__(self, *args, **kwargs): pass
        def get_nanos(self): return 0
        def stop(self): pass

__all__ = ["PtpClock"]

