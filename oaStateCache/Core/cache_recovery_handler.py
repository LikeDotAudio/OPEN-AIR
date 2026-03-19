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
            logger.info(f"🧠💾🛡️ [RECOVERY] Corrupted cache backed up to: {backup_path.name}")
        except Exception as e:
            logger.error(f"  └─ Failed to create backup: {e}")

    # Return the definitive empty state
    return {}
