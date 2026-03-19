# oaTests/Core/DeleteCache.py
#
# Master Factory Reset Script.
# 1. Wipes the local 'DATA' directory (logs, cache, state).
# 2. Wipes the MQTT Broker's retained messages via ClearMQTT.
#
# Dependencies: paho-mqtt
# Usage: python3 DeleteCache.py [--host localhost] [--port 1883]
#
# Author: Anthony Peter Kuzub
# Version 20260222.FactoryReset.1

import os
import shutil
import argparse
import logging
import sys
from pathlib import Path

LOCAL_DEBUG = True    # Set to False in production, True for dev on this file

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("FactoryReset")

def delete_local_data():
    """
    Deletes the entire DATA directory and its contents.
    Recreates the directory structure to avoid application startup errors.
    """
    # oaTests/Core/DeleteCache.py -> project_root
    current_script_dir = Path(__file__).resolve().parent
    project_root = current_script_dir.parents[1]
    
    # ⚡ NEW STRUCTURE: Wipe the refactored oaData* directories
    data_dirs = [
        project_root / "oaDataCache",
        project_root / "oaDataLogs",
        project_root / "oaDataRunningFiles",
        project_root / ".pytest_cache" / "oaDataState",
        # Keep DATA/ for legacy compatibility if it exists
        project_root / "DATA"
    ]

    for data_dir in data_dirs:
        if data_dir.exists():
            if LOCAL_DEBUG: logger.info(f"🗑️  Nuking local storage: {data_dir}")
            try:
                shutil.rmtree(data_dir)
                if LOCAL_DEBUG: logger.info(f"  └─ 💥 {data_dir.name} directory deleted.")
            except Exception as e:
                logger.error(f"  └─ ❌ Failed to delete {data_dir.name}: {e}")
        else:
            if LOCAL_DEBUG: logger.info(f"  └─ 🤷 {data_dir.name} directory not found.")

    # Recreate standard structure via path_initializer
    if LOCAL_DEBUG: logger.info("🌱 Recreating fresh directory structure...")
    try:
        sys.path.insert(0, str(project_root))
        from oaOchestration.Core.path_initializer import initialize_paths
        initialize_paths()
        if LOCAL_DEBUG: logger.info("✨ Directory structure reset successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to recreate directory structure: {e}")

def perform_factory_reset(host, port):
    if LOCAL_DEBUG: logger.info("🚨 INITIATING OPEN-AIR FACTORY RESET 🚨")
    
    # 1. Clear Local Data
    delete_local_data()
    
    # 2. Clear MQTT Broker
    # Import MQTTSweeper dynamically to avoid path issues if run from elsewhere
    try:
        current_dir = Path(__file__).parent
        if str(current_dir) not in sys.path:
            sys.path.append(str(current_dir))
            
        import ClearMQTT
        
        if LOCAL_DEBUG: logger.info("🧹 Handing over to MQTTSweeper...")
        sweeper = ClearMQTT.MQTTSweeper(host, port, "OPEN-AIR")
        sweeper.sweep()
        
    except ImportError:
        logger.error("❌ Could not import ClearMQTT.py. Is it in the same directory?")
    except Exception as e:
        logger.error(f"❌ Failed to run MQTT Sweep: {e}")

    if LOCAL_DEBUG: logger.info("✅ Factory Reset Complete. System is tabula rasa.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OPEN-AIR Factory Reset Tool")
    parser.add_argument("--host", type=str, default="localhost", help="MQTT Broker Host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT Broker Port")
    
    args = parser.parse_args()
    
    perform_factory_reset(args.host, args.port)
