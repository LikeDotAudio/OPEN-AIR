# oaPTP/Methods/ptp_clock.py
# Author: Anthony Peter Kuzub
# Version: 20260331.2130.2
#
# Description: Pure Rust PTP Clock listener (No Python fallback).

import logging
from .oaPTPClock_rs.compiler_hook import ensure_compiled

HAS_RUST = False
try:
    ensure_compiled()
    from oaptpclock_rs import PtpEngine as RustPtpEngine
    HAS_RUST = True
except (ImportError, ModuleNotFoundError):
    logging.warning("⚠️ [PTP] oaptpclock_rs not found. PTP Clock will be disabled.")
except Exception as e:
    logging.error(f"❌ [PTP] Failed to initialize Rust PTP Clock: {e}")

LOCAL_DEBUG = False

class PtpClock:
    """
    High-precision PTP clock listener.
    MANDATORY Rust implementation.
    """
    def __init__(self):
        self._engine = None
        if not HAS_RUST:
            return

        if LOCAL_DEBUG:
            print("🕒🛠️🔗 [PTP] Using PURE RUST clock.")
        try:
            # Note: We use global RustPtpEngine which was imported in the try block
            self._engine = RustPtpEngine()
            self._engine.start()
        except Exception as e:
            logging.error(f"❌ [PTP] Rust engine instantiation failed: {e}")
            self._engine = None

    def get_nanos(self):
        if self._engine:
            return self._engine.get_nanos()
        return 0

    def stop(self):
        if self._engine:
            self._engine.stop()
