import datetime
import shutil

# Core/cache_recovery_handler.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose
from oaLogging.Methods.matrix_gate import matrix_log


def recover_corrupted_cache(filepath, exception):
    """
    Handles state cache corruption by backing up the bad file and returning an empty state.
    """
    matrix_log("core", "data", "recover_corrupted_cache", f"🧠💾🚫 [CACHE CORRUPTED] Critical error loading state cache: {filepath}", "CRITICAL")
    matrix_log("core", "data", "recover_corrupted_cache", f"  └─ Reason: {exception}", "CRITICAL")

    if filepath.exists():
        backup_path = filepath.with_suffix(f".corrupted_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        try:
            shutil.copy(filepath, backup_path)
            matrix_log("core", "data", "recover_corrupted_cache", f"🧠💾🛡️ [RECOVERY] Corrupted cache backed up to: {backup_path.name}", "INFO")
        except Exception as e:
            matrix_log("core", "data", "recover_corrupted_cache", f"  └─ Failed to create backup: {e}", "ERROR")

    # Return the definitive empty state
    return {}
