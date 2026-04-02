# oaPTP/Methods/ptp_clock.py
# Author: Anthony Peter Kuzub
# Version: 20260331.2130.2
#
# Description: Pure Rust PTP Clock listener (No Python fallback).

from .oaPTPClock_rs.compiler_hook import ensure_compiled
ensure_compiled()
from .oaPTPClock_rs.oaptpclock_rs import PtpEngine as RustPtpEngine

LOCAL_DEBUG = False

class PtpClock:
    """
    High-precision PTP clock listener.
    MANDATORY Rust implementation.
    """
    def __init__(self):
        if LOCAL_DEBUG:
            print("🕒🛠️🔗 [PTP] Using PURE RUST clock.")
        self._engine = RustPtpEngine()
        self._engine.start()

    def get_nanos(self):
        return self._engine.get_nanos()

    def stop(self):
        self._engine.stop()
