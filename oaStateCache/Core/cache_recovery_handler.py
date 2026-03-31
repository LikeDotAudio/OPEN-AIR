import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# Core/cache_recovery_handler.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from loguru import logger
import shutil
import datetime

def recover_corrupted_cache(filepath, exception):
    """
    Handles state cache corruption by backing up the bad file and returning an empty state.
    """
    logger.critical(f"🧠💾🚫 [CACHE CORRUPTED] Critical error loading state cache: {filepath}")
    logger.critical(f"  └─ Reason: {exception}")

    if filepath.exists():
        backup_path = filepath.with_suffix(f".corrupted_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        try:
            shutil.copy(filepath, backup_path)
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🧠💾🛡️ [RECOVERY] Corrupted cache backed up to: {backup_path.name}", "INFO")
        except Exception as e:
            logger.error(f"  └─ Failed to create backup: {e}")

    # Return the definitive empty state
    return {}
