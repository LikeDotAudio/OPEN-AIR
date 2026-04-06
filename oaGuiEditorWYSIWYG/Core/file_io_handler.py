import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# Core/file_io_handler.py
# Author: Gemini CLI
# Version: 1.0.0
#
# Description: Handles loading and saving of GUI definition files.

import orjson
import shutil
import datetime
from pathlib import Path
from .state import state_manager
from oaLogging.Core.logger import initialize_logging, set_log_directory



class FileIOHandler:
    """Manages file persistence and backups for the editor."""

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
            matrix_log(
                system="UI",
                element="FILE_IO",
                func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown",
                message=f"💾📁✏️ [FILE_IO] Reading file content ({path.stat().st_size} bytes)...",
                level="debug",
            )
            if path.stat().st_size == 0:
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
                ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                # ⚡ REQUIREMENT: Backup should have the .old extension (archive style)
                backup_path = path.with_name(f"{ts}_{path.stem}.old")
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
