import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# oaTests/Methods/FlameGraph/Entry.py
#
# Unified Entry Point for FlameGraph Performance Profiling.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260329.0010.1
#
# Description:
# This module serves as the primary orchestrator for performance profiling
# sessions using the FlameGraph engine. It initializes the Multi-Threaded
# Profiler, launches the target application (openair.py), and synthesizes
# a forensic HTML report upon completion or critical failure.
#
# Architectural Role:
# - Profiling Orchestrator: Wraps the application lifecycle in a profiling context.
# - Forensic Integrator: Connects the FlameManager with the System Watchdog.

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

from oaTests.Methods.FlameGraph.flame_manager import FlameManager

def main():
    """
    Orchestrates a full profiling session of the OpenAir application.
    """
    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🔥 [ENTRY] Initializing Performance Profiling Session...", "INFO")
    
    manager = FlameManager()
    
    # 1. Start Profiling
    manager.start_profiling()
    
    # 2. Register Panic Callback (Handle "Halting and Catching Fire")
    try:
        from oaWatchdog.Managers.watchdog import register_panic_callback
        # Register a callback to ensure report is generated on critical failure
        register_panic_callback(lambda: manager.generate_report())
        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🔥 [ENTRY] Panic callback registered with Watchdog.", "INFO")
    except ImportError:
        logger.warning("🔥 [ENTRY] Watchdog not found. Panic callbacks disabled.")
    except Exception as e:
        logger.error(f"🔥 [ENTRY] Failed to register panic callback: {e}")

    # 3. Launch the Application
    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🔥 [ENTRY] Launching OpenAir Application...", "INFO")
    try:
        import openair
        # Assuming openair has a main() entry point that starts the app
        # and blocking until the app is closed.
        openair.main()
    except KeyboardInterrupt:
        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🔥 [ENTRY] Session interrupted by user (KeyboardInterrupt).", "INFO")
    except Exception as e:
        logger.exception(f"🔥 [ENTRY] Application crashed during profiling: {e}")
    finally:
        # 4. Stop Profiling and Generate Report
        manager.stop_profiling()
        report_path = manager.generate_report()
        
        if report_path:
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🔥 [ENTRY] Performance profiling session complete.", "SUCCESS")
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🔥 [ENTRY] Report: {report_path}", "INFO")
        else:
            logger.error("🔥 [ENTRY] Failed to synthesize final report.")

if __name__ == "__main__":
    main()
