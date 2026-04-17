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
            message="💾📁✏️ [FILE_IO] SAVE AS SEQUENCE INITIATED.",
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
                message="💾📁✏️ [FILE_IO] SAVE AS CANCELLED by user.",
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
            message=f"💾📁✏️ [FILE_IO] SAVE SEQUENCE INITIATED. Target: {path}",
            level="info",
        )
        
        if not path:
            matrix_log(
                system='UI',
                element='FILE_IO',
                level="warning",
                message="💾📁✏️ [FILE_IO] SAVE ABORTED - No file path set in StateManager.",
                func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown"
            )
            return False
            
        try:
            matrix_log(
                system="UI",
                element="FILE_IO",
                func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown",
                message="💾📁✏️ [FILE_IO] Requesting master state from StateManager...",
                level="debug",
            )
            data = state_manager.get_state()
            
            # 1. Create and Verify Backup
            if path.exists():
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                # ⚡ REQUIREMENT: Backup should have the .old extension (archive style)
                backup_path = path.with_name(f"{timestamp}_{path.stem}.old")
                matrix_log(
                    system="UI",
                    element="FILE_IO",
                    func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown",
                    message=f"💾📁✏️ [FILE_IO] Creating backup copy: {backup_path.name}",
                    level="debug",
                )
                
                # Copy original to backup
                shutil.copy2(path, backup_path)
                
                # 🛡️ VALIDATION: Ensure backup is successful and contains data
                if not backup_path.exists() or backup_path.stat().st_size <= 1:
                    matrix_log(
                        system='UI',
                        element='FILE_IO',
                        level="error",
                        message=f"💾📁✏️ [FILE_IO] BACKUP FAILED or is empty! {backup_path.name}",
                        func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown"
                    )
                    matrix_log(
                        system='UI',
                        element='FILE_IO',
                        level='error',
                        message="💾📁✏️ [FILE_IO] Save sequence ABORTED to prevent data loss.",
                        func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown"
                    )
                    return False
                
                matrix_log(system="UI", element="FILE_IO", func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", message=f"💾📁✏️ [FILE_IO] Backup verified ({backup_path.stat().st_size} bytes): {backup_path.name}", level="INFO")
            
            # 2. Save Data (using binary mode for orjson)
            matrix_log(system="UI", element="FILE_IO", func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", message=f"💾📁✏️ [FILE_IO] Writing JSON to {path.name}...", level="DEBUG")
            with open(path, 'wb') as f:
                f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
                
            matrix_log(system="UI", element="FILE_IO", func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", message=f"💾📁✏️ [FILE_IO] File successfully written and closed: {path.name}", level="SUCCESS")
            
            if on_save_callback:
                matrix_log(system="UI", element="FILE_IO", func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", message=f"💾📁✏️ [FILE_IO] Executing on_save_callback...", level="DEBUG")
                on_save_callback()
                
            return True
        except Exception as e:
            matrix_log(
                system='UI',
                element='FILE_IO',
                level='exception',
                message=f"💾📁✏️ [FILE_IO] Failed to save file: {e}",
                func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown",
            )
            return False
