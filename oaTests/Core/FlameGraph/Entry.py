# FlameGraph/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Unified Entry Point for FlameGraph Performance Profiling.

import sys
import os
import pathlib
import threading
from loguru import logger

# 1. Setup Environment
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaTests.Core.FlameGraph.flame_manager import FlameManager

def main():
    """
    Orchestrates a full profiling session of the OpenAir application.
    """
    logger.info("🔥 [ENTRY] Initializing Performance Profiling Session...")
    
    manager = FlameManager()
    
    # 1. Start Profiling
    manager.start_profiling()
    
    # 2. Register Panic Callback (Handle "Halting and Catching Fire")
    try:
        from oaWatchdog.Managers.watchdog import register_panic_callback
        # Register a callback to ensure report is generated on critical failure
        register_panic_callback(lambda: manager.generate_report())
        logger.info("🔥 [ENTRY] Panic callback registered with Watchdog.")
    except ImportError:
        logger.warning("🔥 [ENTRY] Watchdog not found. Panic callbacks disabled.")
    except Exception as e:
        logger.error(f"🔥 [ENTRY] Failed to register panic callback: {e}")

    # 3. Launch the Application
    logger.info("🔥 [ENTRY] Launching OpenAir Application...")
    try:
        import OpenAir
        # Assuming OpenAir has a main() entry point that starts the app
        # and blocking until the app is closed.
        OpenAir.main()
    except KeyboardInterrupt:
        logger.info("🔥 [ENTRY] Session interrupted by user (KeyboardInterrupt).")
    except Exception as e:
        logger.exception(f"🔥 [ENTRY] Application crashed during profiling: {e}")
    finally:
        # 4. Stop Profiling and Generate Report
        manager.stop_profiling()
        report_path = manager.generate_report()
        
        if report_path:
            logger.success(f"🔥 [ENTRY] Performance profiling session complete.")
            logger.info(f"🔥 [ENTRY] Report: {report_path}")
        else:
            logger.error("🔥 [ENTRY] Failed to synthesize final report.")

if __name__ == "__main__":
    main()
