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
from loguru import logger



class FileIOHandler:
    """Manages file persistence and backups for the editor."""

    @staticmethod
    def load_file(filepath):
        """Loads a JSON file and initializes the state manager."""
        path = Path(filepath)
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"📁 FileIOHandler: Load operation started for: {filepath}", "INFO")
        
        if not path.exists():
            logger.error(f"❌ FileIOHandler: File not found: {filepath}")
            return False
            
        try:
            matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"📁 FileIOHandler: Reading file content ({path.stat().st_size} bytes)...", "DEBUG")
            with open(path, 'rb') as f:
                data = orjson.loads(f.read())
            
            matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"📁 FileIOHandler: File parsed successfully. Initializing StateManager...", "SUCCESS")
            state_manager.initialize(data, file_path=path)
            matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"✅ FileIOHandler: Successfully loaded and initialized state from {path.name}", "SUCCESS")
            return True
        except Exception as e:
            logger.exception("❌ FileIOHandler Error: Failed to load {filepath}")
            return False

    @staticmethod
    def save_file(on_save_callback=None):
        """Saves the current state to disk with an automatic backup."""
        path = state_manager.get_file_path()
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"📁 FileIOHandler: SAVE SEQUENCE INITIATED. Target: {path}", "INFO")
        
        if not path:
            logger.warning("⚠️ FileIOHandler: SAVE ABORTED - No file path set in StateManager.")
            return False
            
        try:
            matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "📁 FileIOHandler: Requesting master state from StateManager...", "DEBUG")
            data = state_manager.get_state()
            
            # 1. Create and Verify Backup
            if path.exists():
                ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                # ⚡ REQUIREMENT: Backup should have the .old extension (archive style)
                backup_path = path.with_name(f"{ts}_{path.stem}.old")
                matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"📦 FileIOHandler: Creating backup copy: {backup_path.name}", "DEBUG")
                
                # Copy original to backup
                shutil.copy2(path, backup_path)
                
                # 🛡️ VALIDATION: Ensure backup is successful and contains data
                if not backup_path.exists() or backup_path.stat().st_size <= 1:
                    logger.error(f"❌ FileIOHandler: BACKUP FAILED or is empty! {backup_path.name}")
                    logger.error("🛑 FileIOHandler: Save sequence ABORTED to prevent data loss.")
                    return False
                
                matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"📦 FileIOHandler: Backup verified ({backup_path.stat().st_size} bytes): {backup_path.name}", "INFO")
            
            # 2. Save Data (using binary mode for orjson)
            matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💾 FileIOHandler: Writing JSON to {path.name}...", "DEBUG")
            with open(path, 'wb') as f:
                f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
                
            matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💾 FileIOHandler: File successfully written and closed: {path.name}", "SUCCESS")
            
            if on_save_callback:
                matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "📁 FileIOHandler: Executing on_save_callback...", "DEBUG")
                on_save_callback()
                
            return True
        except Exception as e:
            logger.exception("❌ FileIOHandler Error: Failed to save file")
            return False
