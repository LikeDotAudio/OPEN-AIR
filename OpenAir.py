#!/usr/bin/env python3
# /OpenAir.py
#
# The Supervisor Entry Point for OPEN-AIR.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/catego
# ry/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260314.120000.REV01

"""
OpenAir.py - The Multi-Process Supervisor for the OPEN-AIR System.

Purpose:
    Acts as the master process (Supervisor) that orchestrates the execution
    of the partitioned OPEN-AIR architecture. It is responsible for spawning
    and monitoring Partition A (Core) and Partition B (UI) as independent 
    OS-level processes.

Responsibilities:
    - Establish a randomized Session Identity (GUID) for the current run.
    - Initialize base system paths and early supervisor-level logging.
    - Spawn child processes for the Core and UI partitions with injected
      environment identities.
    - Monitor child process liveness and implement restart logic for 
      mission-critical deployments.
    - Manage a coordinated shutdown sequence to ensure no "zombie" processes
      remain on the system.

Constraints:
    - Requires a Python 3.x environment.
    - Assumes the presence of 'managers/System_Core/open_air_core.py' and 
      'managers/Display/open_air_ui.py'.
    - Relies on 'subprocess.Popen' for process isolation; behaviors may 
      vary slightly between Linux and Windows process management.
"""

import sys
import os
import time
import subprocess
import pathlib
import signal

# Ensure the root directory is in the search path for local module imports.
current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

from oaLogging.logger import initialize_logging, set_log_directory
from loguru import logger
from oaOchestration.path_initializer import initialize_paths, DATA_LOGS_DIR
from oaConfiguration.config_reader import Config

# _DEBUG: Internal flag to toggle verbose supervisor logging.
_DEBUG = True

def main():
    """
    Executes the supervisor lifecycle: Setup -> Spawn -> Monitor -> Shutdown.

    Lead with action: Orchestrates the dual-partition boot sequence. It 
    first resolves system paths, then launches the UI and Core as 
    subprocesses, and finally enters a monitoring loop.

    Inputs:
        sys.argv: Accepts '--core' or '--ui' to bypass the supervisor and
                 launch a specific partition directly (for debugging).

    Outputs:
        None. Process terminates on child exit or manual interrupt.

    Side Effects:
        - Spawns multiple child processes.
        - Modifies the system environment for child processes.
        - Writes logs to the 'oaDataLogs' directory.
    """
    # Handle direct partition launching for developer convenience.
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "--core":
            try:
                import oaComBroker.Core.open_air_core as core_mod
            except ImportError:
                import oaComBroker.open_air_core as core_mod
            core_mod.main()
            return
        elif mode == "--ui":
            try:
                import oaGuiManager.open_air_ui as ui_mod
            except ImportError:
                import oaGuiManager.Core.open_air_ui as ui_mod
            ui_mod.main()
            return

    # --- Supervisor Setup ---
    initialize_paths()
    log_dir = DATA_LOGS_DIR
    set_log_directory(log_dir, partition="SUP")
    
    app_config = Config.get_instance()
    is_mission_critical = app_config.MISSION_CRITICAL_MODE

    def log(msg):
        """Internal helper for consistent supervisor console output."""
        print(f"[SUPERVISOR] {msg}")
        if _DEBUG: 
            logger.debug(f"🚀 SUPERVISOR: {msg}")

    log(f"Launching OPEN-AIR Partitions... (Mission Critical: {is_mission_critical})")

    python_executable = sys.executable
    
    # Core Partition (Communication & Logic)
    core_script = os.path.join(current_dir, "oaComBroker", "Core", "open_air_core.py")
    if not os.path.exists(core_script):
        core_script = os.path.join(current_dir, "oaComBroker", "open_air_core.py")
        
    # UI Partition (Display & Interaction)
    ui_script = os.path.join(current_dir, "oaGuiManager", "open_air_ui.py")
    if not os.path.exists(ui_script):
        # Handle potential future realignment of GuiManager
        ui_script_alt = os.path.join(current_dir, "oaGuiManager", "Core", "open_air_ui.py")
        if os.path.exists(ui_script_alt):
            ui_script = ui_script_alt

    def get_host_guid():
        """Generates a non-persistent, 64-bit session identifier."""
        return os.urandom(8).hex().upper()

    session_guid = get_host_guid()
    log(f"Session Identity established (Randomized): {session_guid}")
    
    # Clone the current environment and inject the session GUID.
    child_env = os.environ.copy()
    child_env["OPEN_AIR_INSTANCE_GUID"] = session_guid

    # Define partition-specific environment variables.
    core_env = child_env.copy()
    core_env["OPEN_AIR_PARTITION_ID"] = "CORE"
    
    ui_env = child_env.copy()
    ui_env["OPEN_AIR_PARTITION_ID"] = "UI"

    processes = []
    p_core = None
    p_ui = None

    # Use a flag for graceful shutdown instead of catching KeyboardInterrupt
    shutdown_requested = [False]
    def signal_handler(sig, frame):
        log("🛑 Keyboard Interrupt (Signal). Initiating graceful shutdown...")
        shutdown_requested[0] = True

    signal.signal(signal.SIGINT, signal_handler)

    # 1. Launch UI Partition (Handles User Feedback/Splash Screen).
    log("Spawning Partition B (UI)...")
    p_ui = subprocess.Popen([python_executable, ui_script], env=ui_env)
    processes.append(p_ui)
    
    # 2. Launch Core Partition (Handles Hardware/Logic).
    log("Spawning Partition A (Core)...")
    p_core = subprocess.Popen([python_executable, core_script], env=core_env)
    # Core is prioritized in the monitoring list at index 0.
    processes.insert(0, p_core)
    
    log("System Running. Monitoring child processes...")

    # --- Monitoring Loop ---
    while not shutdown_requested[0]:
        time.sleep(0.5) # Throttle loop to minimize CPU impact.
        
        # Check Core partition liveness.
        if p_core.poll() is not None:
            if is_mission_critical and not shutdown_requested[0]:
                log(f"❌ Core died (Code {p_core.returncode}). Restarting in 1s...")
                time.sleep(1.0) # ⚡ OPTIMIZATION: Throttled restart backoff
                p_core = subprocess.Popen([python_executable, core_script], 
                                            env=core_env)
                processes[0] = p_core
            else:
                log(f"🛑 Core exited (Code {p_core.returncode}). Shutting down.")
                break
        
        # Check UI partition liveness.
        if p_ui.poll() is not None:
            if is_mission_critical and not shutdown_requested[0]:
                log(f"⚠️ UI exited (Code {p_ui.returncode}). Restarting in 1s...")
                time.sleep(1.0) # ⚡ OPTIMIZATION: Throttled restart backoff
                p_ui = subprocess.Popen([python_executable, ui_script], 
                                            env=ui_env)
                processes[1] = p_ui
            else:
                log(f"👋 UI exited (Code {p_ui.returncode}). System complete.")
                break

    # --- Finalization and Cleanup ---
    log("Terminating child processes...")
    for p in processes:
        if p and p.poll() is None:
            p.terminate()
            # Polling instead of p.wait(timeout=2) to avoid exception
            start_wait = time.time()
            while p.poll() is None and (time.time() - start_wait) < 2:
                time.sleep(0.1)
            
            if p.poll() is None:
                # Force-kill if the process refuses to terminate within 2s.
                p.kill()
                p.wait() # Final wait to clean up zombie
    log("Supervisor shutdown complete. Goodbye.")

if __name__ == "__main__":
    main()
