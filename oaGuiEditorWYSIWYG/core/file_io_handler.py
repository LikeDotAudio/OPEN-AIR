# workers/wysiwyg_editor/core/file_io_handler.py
#
# Handles loading and saving of GUI definition files.
# Manages backups and provides integration with the State Manager.
#
# Author: Gemini CLI

import orjson
import shutil
import datetime
from pathlib import Path
from .state import state_manager
from oaLogging.logger import initialize_logging, set_log_directory
from loguru import logger

LOCAL_DEBUG = True    # Set to False in production, True for dev on this file


class FileIOHandler:
    """Manages file persistence and backups for the editor."""

    @staticmethod
    def load_file(filepath):
        """Loads a JSON file and initializes the state manager."""
        path = Path(filepath)
        if LOCAL_DEBUG: logger.info(f"📁 FileIOHandler: Load operation started for: {filepath}")
        
        if not path.exists():
            logger.error(f"❌ FileIOHandler: File not found: {filepath}")
            return False
            
        try:
            if LOCAL_DEBUG: logger.debug(f"📁 FileIOHandler: Reading file content ({path.stat().st_size} bytes)...")
            with open(path, 'rb') as f:
                data = orjson.loads(f.read())
            
            if LOCAL_DEBUG: logger.success(f"📁 FileIOHandler: File parsed successfully. Initializing StateManager...")
            state_manager.initialize(data, file_path=path)
            if LOCAL_DEBUG: logger.success(f"✅ FileIOHandler: Successfully loaded and initialized state from {path.name}")
            return True
        except Exception as e:
            logger.exception("❌ FileIOHandler Error: Failed to load {filepath}")
            return False

    @staticmethod
    def save_file(on_save_callback=None):
        """Saves the current state to disk with an automatic backup."""
        path = state_manager.get_file_path()
        if LOCAL_DEBUG: logger.info(f"📁 FileIOHandler: SAVE SEQUENCE INITIATED. Target: {path}")
        
        if not path:
            logger.warning("⚠️ FileIOHandler: SAVE ABORTED - No file path set in StateManager.")
            return False
            
        try:
            if LOCAL_DEBUG: logger.debug("📁 FileIOHandler: Requesting master state from StateManager...")
            data = state_manager.get_state()
            
            # 1. Create and Verify Backup
            if path.exists():
                ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                backup_path = path.with_name(f"{ts}_{path.name}")
                if LOCAL_DEBUG: logger.debug(f"📦 FileIOHandler: Creating backup copy: {backup_path.name}")
                
                # Copy original to backup
                shutil.copy2(path, backup_path)
                
                # 🛡️ VALIDATION: Ensure backup is successful and contains data
                if not backup_path.exists() or backup_path.stat().st_size <= 1:
                    logger.error(f"❌ FileIOHandler: BACKUP FAILED or is empty! {backup_path.name}")
                    logger.error("🛑 FileIOHandler: Save sequence ABORTED to prevent data loss.")
                    return False
                
                if LOCAL_DEBUG: logger.info(f"📦 FileIOHandler: Backup verified ({backup_path.stat().st_size} bytes): {backup_path.name}")
            
            # 2. Save Data (using binary mode for orjson)
            if LOCAL_DEBUG: logger.debug(f"💾 FileIOHandler: Writing JSON to {path.name}...")
            with open(path, 'wb') as f:
                f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
                
            if LOCAL_DEBUG: logger.success(f"💾 FileIOHandler: File successfully written and closed: {path.name}")
            
            if on_save_callback:
                if LOCAL_DEBUG: logger.debug("📁 FileIOHandler: Executing on_save_callback...")
                on_save_callback()
                
            return True
        except Exception as e:
            logger.exception("❌ FileIOHandler Error: Failed to save file")
            return False
