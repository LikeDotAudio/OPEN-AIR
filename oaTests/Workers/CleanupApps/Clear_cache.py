# oaTests/Workers/CleanupApps/Clear_cache.py
# Author: Anthony Peter Kuzub
# Version: 20260407.2345.1
#
# Description: Master Cache Purge Script. Ensures a clean slate for MQTT-driven state.

import sys
import shutil
import logging
from pathlib import Path

# 1. Setup Environment
current_script_dir = Path(__file__).resolve().parent
project_root = current_script_dir.parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaLogging.Methods.matrix_gate import matrix_log

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("CachePurge")

def purge_cache():
    """
    Deletes the local cache and running state files.
    Excludes application logs but targets stateful data.
    """
    # Target non-log data directories and stateful logs
    data_dirs = [
        project_root / "oaDataCache",
        project_root / "oaDataRunningFiles",
        project_root / "oaDataSplinks",
        project_root / "oaDataLogs" / "Reports",
        project_root / ".pytest_cache" / "RUN",
        project_root / "DATA" # Legacy compatibility
    ]
    
    # Specific files to remove
    target_files = [
        project_root / "oaDataCache" / "device_state_cache.json",
        project_root / "oaDataCache" / "layout_cache.json",
        project_root / "oaComProtocols" / "oaComSNMP" / "Assets" / "current.mib",
        project_root / "oaComProtocols" / "oaComSNMP" / "Assets" / "OPEN-AIR.mib",
        project_root / "oaComProtocols" / "oaComSNMP" / "Assets" / "openair_snmp_objects.txt",
        project_root / "oaComProtocols" / "oaComSNMP" / "Assets" / "openair_snmp_set.log",
        project_root / "oaComProtocols" / "oaComSNMP" / "Assets" / "bridge_debug.log"
    ]

    matrix_log("core", "system", "purge_cache", "📡📤📤 [CLEAR_CACHE] Starting local cache and state purge...", "INFO")

    # 1. Clean individual files
    for f in target_files:
        if f.exists():
            f.unlink()
            matrix_log("core", "system", "purge_cache", f"🗑️  Deleted: {f.name}", "INFO")

    # 2. Clean directories
    for data_dir in data_dirs:
        if data_dir.exists():
            matrix_log("core", "system", "purge_cache", f"🗑️  Nuking contents of: {data_dir.name}", "INFO")
            try:
                # To delete CONTENTS and not the dir itself (to preserve permissions/structure)
                items_purged = 0
                for item in data_dir.iterdir():
                    try:
                        if item.is_file() or item.is_symlink():
                            item.unlink()
                            items_purged += 1
                        elif item.is_dir():
                            shutil.rmtree(item)
                            items_purged += 1
                    except Exception as e:
                        logger.error(f"  └─ ❌ Failed to delete {item.name}: {e}")
                
                if items_purged > 0:
                    matrix_log("core", "system", "purge_cache", f"  └─ 💥 Purged {items_purged} items from {data_dir.name}.", "INFO")
            except Exception as e:
                logger.error(f"  └─ ❌ Failed to access {data_dir.name}: {e}")
        else:
            matrix_log("core", "system", "purge_cache", f"  └─ 🤷 {data_dir.name} directory not found.", "INFO")

    # Recreate structure via path_initializer to ensure sanity
    matrix_log("core", "system", "purge_cache", "🌱 Re-initializing directory structure integrity...", "INFO")
    try:
        from oaOchestration.Core.path_initializer import initialize_paths
        initialize_paths()
        matrix_log("core", "system", "purge_cache", "✨ Directory structure integrity verified.", "INFO")
    except Exception as e:
        logger.error(f"❌ Failed to initialize paths: {e}")

    # 3. Clear in-memory state cache to prevent automatic recreation with old data
    try:
        import oaStateCache.Entry as StateCacheEntry
        registry = StateCacheEntry.get_registry()
        if registry and hasattr(registry, "clear_all_state"):
            matrix_log("core", "system", "purge_cache", "🧠 Wiping in-memory State Registry...", "INFO")
            registry.clear_all_state()
            matrix_log("core", "system", "purge_cache", "🧠 In-memory State Registry wiped.", "INFO")
    except Exception as e:
        logger.error(f"  └─ ❌ Failed to clear in-memory state cache: {e}")

    # 4. Notify distributed processes via MQTT
    try:
        import paho.mqtt.publish as publish
        matrix_log("core", "system", "purge_cache", "📡 Broadcasting global cache clear command...", "INFO")
        publish.single("OPEN-AIR/System/Control/ClearCache", "true", hostname="localhost", port=1883)
    except Exception as e:
        logger.warning(f"  └─ ⚠️ Failed to broadcast MQTT clear cache command: {e}")

    matrix_log("core", "system", "purge_cache", "📡📤📤 [CLEAR_CACHE] Cache purge complete.", "INFO")

if __name__ == "__main__":
    purge_cache()
