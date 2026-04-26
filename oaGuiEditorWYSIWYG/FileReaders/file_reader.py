# FileReaders/file_reader.py
# Author: Gemini CLI
# Version: 1.0.0
#
# Description: Handles loading of GUI definition files.

import inspect
from pathlib import Path
from tkinter import filedialog

import orjson

from oaLogging.Methods.matrix_gate import matrix_log

from ..Core.state import state_manager


class FileReader:
    """Manages file reading for the editor."""

    @staticmethod
    def open_file():
        """Opens a file dialog to select a JSON file and loads it."""
        filepath = filedialog.askopenfilename(
            title="Open GUI Definition",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if filepath:
            return FileReader.load_file(filepath)
        return False

    @staticmethod
    def load_file(filepath):
        """Loads a JSON file and initializes the state manager."""
        path = Path(filepath)
        matrix_log(
            system="UI",
            element="FILE_IO",
            func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown",
            message=f"💾📁✏️ [FILE_IO] Load operation started for: {filepath}",
            level="info",
        )

        if not path.exists():
            matrix_log(
                system='UI',
                element='FILE_IO',
                level="error",
                message=f"💾📁✏️ [FILE_IO] File not found: {filepath}",
                func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown"
            )
            return False

        try:
            file_size = path.stat().st_size
            matrix_log(
                system="UI",
                element="FILE_IO",
                func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown",
                message=f"💾📁✏️ [FILE_IO] Reading file content ({file_size} bytes)...",
                level="debug",
            )
            if file_size > 50 * 1024 * 1024:
                matrix_log(system="UI", element="FILE_IO", level="error", message="💾📁✏️ [FILE_IO] File exceeds 50MB safety limit.", func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown")
                return False
            if file_size == 0:
                matrix_log(
                    system="UI",
                    element="FILE_IO",
                    func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown",
                    message="💾📁✏️ [FILE_IO] File is empty. Initializing with empty dict.",
                    level="warning",
                )
                data = {}
            else:
                with open(path, 'rb') as f:
                    data = orjson.loads(f.read())

            matrix_log(
                system="UI",
                element="FILE_IO",
                func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown",
                message="💾📁✏️ [FILE_IO] File parsed successfully. Initializing StateManager...",
                level="info",
            )
            state_manager.initialize(data, file_path=path)
            matrix_log(
                system="UI",
                element="FILE_IO",
                func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown",
                message=f"💾📁✏️ [FILE_IO] Successfully loaded and initialized state from {path.name}",
                level="info",
            )
            return True
        except Exception as e:
            matrix_log(
                system='UI',
                element='FILE_IO',
                level="exception",
                message=f"💾📁✏️ [FILE_IO] Failed to load {filepath}: {e}",
                func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown",
            )
            return False
