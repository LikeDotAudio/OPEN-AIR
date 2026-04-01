# oaGuiManager/Core/fast_scanner.py
# Author: Anthony Peter Kuzub
# Version: 20260331.2350.1
#
# Description: Python wrapper for the Rust Fast Scanner.

import logging
from .oaFastScanner_rs.compiler_hook import ensure_compiled

try:
    ensure_compiled()
    from .oaFastScanner_rs.oafastscanner_rs import FastScanner as RustFastScanner
    HAS_RUST = True
except Exception as e:
    logging.error(f"oaGuiManager: Failed to load Rust Fast Scanner: {e}")
    HAS_RUST = False

class FastScanner:
    """
    High-performance concurrent directory scanner using Rust.
    """
    def __init__(self):
        if HAS_RUST:
            print("📂🛠️🔗 [GUI_MANAGER] Using PURE RUST fast scanner.")
            self._scanner = RustFastScanner()
        else:
            self._scanner = None
            logging.error("oaGuiManager: Missing mandatory Rust fast scanner.")

    def scan_directory(self, root_path: str, suffix: str):
        if self._scanner:
            return self._scanner.scan_directory(root_path, suffix)
        return []
