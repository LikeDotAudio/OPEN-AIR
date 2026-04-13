# oaComProtocols.oaComVisa/Methods/visa_formatter.py
# Author: Anthony Peter Kuzub
# Version: 20260331.2030.2
#
# Description: Pure Rust VISA SCPI formatter (No Python fallback).
try:
    from oaRustCore.oa_visa_format_rs import VisaFormatter as RustVisaFormatter
    HAS_RUST_VISA = True
except ImportError:
    HAS_RUST_VISA = False

LOCAL_DEBUG = False

class VisaFormatter:
    """
    High-performance VISA SCPI command formatter.
    """
    def __init__(self):
        if LOCAL_DEBUG:
            print("💳🛠️🔗 [VISA] Using Rust formatter.")
        self._formatter = RustVisaFormatter() if HAS_RUST_VISA else None

    def format_command(self, cmd: str, value: float):
        return self._formatter.format_command(cmd, value)

    def format_bool(self, cmd: str, value: bool):
        return self._formatter.format_bool(cmd, value)
