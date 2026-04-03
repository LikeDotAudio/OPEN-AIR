# oaGuiManager/Core/fast_scanner.py
# Author: Anthony Peter Kuzub
# Version: 20260331.2350.1
#
# Description: Python wrapper for the Rust Fast Scanner.

LOCAL_DEBUG = True

import logging
from .oaFastScanner_rs.compiler_hook import ensure_compiled

try:
    ensure_compiled()
    from oafastscanner_rs import FastScanner as RustFastScanner
    HAS_RUST = True
except ImportError:
    logging.warning("⚠️ [GUI_MANAGER] oafastscanner_rs not found. Falling back to slow Python directory scanning (if implemented).")
    HAS_RUST = False
except Exception as e:
    logging.error(f"❌ [GUI_MANAGER] Failed to initialize Rust Fast Scanner: {e}")
    HAS_RUST = False

class FastScanner:
    """
    High-performance directory scanner using Rust.
    """
    def __init__(self):
        self._scanner = None
        if not HAS_RUST:
            return

        if LOCAL_DEBUG:
            print("📂🛠️🔗 [GUI_MANAGER] Using PURE RUST fast scanner.")
        try:
            self._scanner = RustFastScanner()
        except Exception as e:
            logging.error(f"❌ [GUI_MANAGER] Rust scanner instantiation failed: {e}")
            self._scanner = None

    def scan_directory(self, root_path: str, suffix: str):
        if self._scanner:
            try:
                return self._scanner.scan_directory(root_path, suffix)
            except Exception as e:
                logging.error(f"❌ [GUI_MANAGER] Rust scanning failed: {e}")
                return []
        return []

