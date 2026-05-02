# oaGui/FileReaders/folder_fast_io_utility.py
# Author: Anthony Peter Kuzub
# Version: 20260331.2350.2
#
# Description: Python wrapper for the Rust Fast Scanner.

LOCAL_DEBUG = False

import logging

try:
    from oaRustCore.oa_fast_scanner_rs import FastScanner as RustFastScanner
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

        try:
            self._scanner = RustFastScanner()
        except Exception as e:
            logging.error(f"❌ [GUI_MANAGER] Failed to instantiate Rust Fast Scanner: {e}")
            self._scanner = None

    def scan_directory(self, root_path: str, extension: str = None) -> list:
        """
        Scans a directory for files with a specific extension.
        """
        if self._scanner:
            try:
                return self._scanner.scan_directory(root_path, extension or "")
            except Exception as e:
                logging.error(f"❌ [GUI_MANAGER] Rust scanning failed: {e}")

        # Python fallback (Simple recursive scan)
        import pathlib
        path = pathlib.Path(root_path)
        if extension:
            return [str(f) for f in path.rglob(f"*{extension}") if f.is_file()]
        return [str(f) for f in path.rglob("*") if f.is_file()]
