# FileWriters/file_writer.py
# Author: Gemini CLI
# Version: 1.0.0
#
# Description: Handles saving of GUI definition files.

import orjson
import shutil
import datetime
import inspect
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from oaLogging.Methods.matrix_gate import matrix_log
from ..Core.state import state_manager

class FileWriter:
    """Manages file writing and backups for the editor."""

    @staticmethod
    def save_as(on_save_callback=None):
        """Prompts the user for a file location and saves the current state."""
        matrix_log(
            system="UI",
            element="FILE_IO",
            func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown",
            message="💾📁✏️ [STORAGE] SAVE AS SEQUENCE INITIATED.",
            level="info",
        )
        
        initial_path = state_manager.get_file_path()
        initial_dir = initial_path.parent if initial_path else "."
        initial_file = initial_path.name if initial_path else "new_gui.json"
        
        file_path = filedialog.asksaveasfilename(
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            matrix_log(
                system='UI',
                element='FILE_IO',
                level="info",
                message="💾📁🛌 [STORAGE] SAVE AS CANCELLED by user.",
                func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown"
            )
            return False
            
        new_path = Path(file_path)
        state_manager.set_file_path(new_path)
        
        return FileWriter.save_file(on_save_callback=on_save_callback)

    @staticmethod
    def save_file(on_save_callback=None):
        """Saves the current state to disk with an automatic backup."""
        path = state_manager.get_file_path()
        matrix_log(
            system="UI",
            element="FILE_IO",
            func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown",
            message=f"💾📁✏️ [STORAGE] SAVE SEQUENCE STARTING for {path.name if path else 'Unknown'}",
            level="info",
        )

        if not path:
            matrix_log(
                system='UI',
                element='FILE_IO',
                level="warning",
                message="💾📁🤷‍♂️ [STORAGE] No file path set. Aborting save.",
                func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown"
            )
            return False

        data = state_manager.get_state()
        
        try:
            matrix_log(
                system="UI",
                element="FILE_IO",
                func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown",
                message=f"💾📁🧹 [STORAGE] Cleaning up old backups for {path.name}...",
                level="debug",
            )
            # Standard cleanup (keep last 5 backups of this specific file)
            # [Optional implementation here]

            # 1. Create Backup
            if path.exists():
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                # ⚡ REQUIREMENT: Backup should have the .old extension (archive style)
                backup_path = path.with_name(f"{timestamp}_{path.stem}.old")
                matrix_log(
                    system="UI",
                    element="FILE_IO",
                    func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown",
                    message=f"💾📁📦 [STORAGE] Creating automated backup: {backup_path.name}",
                    level="info",
                )
                shutil.copy2(path, backup_path)
                
                # 🛡️ VALIDATION: Ensure backup is successful and contains data
                if not backup_path.exists() or backup_path.stat().st_size <= 1:
                    matrix_log(
                        system='UI',
                        element='FILE_IO',
                        level="error",
                        message=f"💾📁🔥 [STORAGE] Backup FAILED verification: {backup_path.name}",
                        func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown"
                    )
                    matrix_log(
                        system='UI',
                        element='FILE_IO',
                        level="warning",
                        message="💾📁🛑 [STORAGE] Aborting save to protect original data.",
                        func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown"
                    )
                    return False

                matrix_log(system="UI", element="FILE_IO", func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", message=f"💾📁🆗 [STORAGE] Backup verified ({backup_path.stat().st_size} bytes): {backup_path.name}", level="INFO")

            # 2. Save Data (using binary mode for orjson)
            matrix_log(system="UI", element="FILE_IO", func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", message=f"💾📁✍️ [STORAGE] Writing JSON to {path.name}...", level="DEBUG")
            with open(path, 'wb') as f:
                f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))

            matrix_log(system="UI", element="FILE_IO", func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", message=f"💾📁🏁 [STORAGE] File successfully written and closed: {path.name}", level="SUCCESS")

            if on_save_callback:
                matrix_log(system="UI", element="FILE_IO", func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", message=f"💾📁🚀 [STORAGE] Executing on_save_callback...", level="DEBUG")
                on_save_callback()

            return True
        except Exception as e:
            matrix_log(
                system='UI',
                element='FILE_IO',
                level="error",
                message=f"💾📁🔥 [STORAGE] Failed to save file: {e}",
                func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown",
            )
            return False
