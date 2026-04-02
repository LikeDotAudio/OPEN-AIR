# oaComVisa/Methods/visa_formatter.py
# Author: Anthony Peter Kuzub
# Version: 20260331.2030.2
#
# Description: Pure Rust VISA SCPI formatter (No Python fallback).

from .oaVisaFormat_rs.compiler_hook import ensure_compiled
ensure_compiled()
from .oaVisaFormat_rs.oavisaformat_rs import VisaFormatter as RustVisaFormatter

LOCAL_DEBUG = False

class VisaFormatter:
    """
    High-performance VISA SCPI command formatter.
    MANDATORY Rust implementation.
    """
    def __init__(self):
        if LOCAL_DEBUG:
            print("💳🛠️🔗 [VISA] Using PURE RUST formatter.")
        self._formatter = RustVisaFormatter()

    def format_command(self, cmd: str, value: float):
        return self._formatter.format_command(cmd, value)

    def format_bool(self, cmd: str, value: bool):
        return self._formatter.format_bool(cmd, value)
