import pathlib
import os
import sys
project_root = pathlib.Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# openair.py
# Author: Anthony Peter Kuzub
# Version: 20260328.0.1
#
# Description: The Supervisor Entry Point for OPEN-AIR.

"""
openair.py - The Multi-Process Supervisor for the OPEN-AIR System.

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
    - Assumes the presence of 'oaComBroker/Core/open_air_core.py' and 
      'oaGuiManager/Managers/open_air_ui.py'.
"""

import time
import subprocess
import signal

# Ensure the root directory is in the search path for local module imports.
# Since this script is in the project root, project_root IS the parent directory.
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger
from oaOchestration.Core.path_initializer import initialize_paths
from oaConfigurationManager.FileReaders.config_reader import Config

# _DEBUG: Internal flag to toggle verbose supervisor logging.
_DEBUG = False

def main():
    """
    Executes the supervisor lifecycle: Setup -> Spawn -> Monitor -> Shutdown.

    Lead with action: Orchestrates the dual-partition boot sequence. It 
    first resolves system paths, then launches the UI and Core as 
    subprocesses, and finally enters a monitoring loop.

    Inputs:
        sys.argv: Accepts '--core' o
        r '--ui' to bypass the supervisor and
                 launch a specific partition directly (for debugging).

    Outputs:
        None. Process terminates on child exit or manual interrupt.

    Side Effects:
        - Spawns multiple child processes.
        - Modifies the system environment for child processes.
        - Writes logs to the 'debug/SUP' directory.
    """
    # Handle direct partition launching for developer convenience.
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "--core":
            import oaComBroker.Core.open_air_core as core_mod
            core_mod.main()
            return
        elif mode == "--ui":
            import oaGuiManager.Managers.open_air_ui as ui_mod
            ui_mod.main()
            return

    # --- Supervisor Setup ---
    GLOBAL_PROJECT_ROOT, data_dir = initialize_paths()
    log_dir = pathlib.Path(data_dir) / "oaDataLogs"
    set_log_directory(log_dir, partition="SUP")
    
    app_config = Config.get_instance()
    is_mission_critical = app_config.MISSION_CRITICAL_MODE

    def log(msg):
        """Internal helper for consistent supervisor console output."""
        # ⚡ V3.1.27 LOG SCRUBBING:
        # Remove ANSI escape sequences from the message before printing to the console.
        # This prevents terminal feedback loops if the output is being captured/piped.
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_msg = ansi_escape.sub('', str(msg))
        
        print(f"[SUPERVISOR] {clean_msg}")
        if _DEBUG: 
            # Keep original message for matrix_log as it supports colorization
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🚀 SUPERVISOR: {msg}", "DEBUG")

    log(f"Launching OPEN-AIR Partitions... (Mission Critical: {is_mission_critical})")

    python_executable = sys.executable
    core_script = project_root / "oaComBroker" / "Core" / "open_air_core.py"
    ui_script = project_root / "oaGuiManager" / "Managers" / "open_air_ui.py"

    # ⚡ VALIDATION: Ensure critical scripts exist before spawning.
    if not core_script.exists():
        log(f"🛑 CRITICAL FAILURE: Core script not found at {core_script}")
        sys.exit(1)
    if not ui_script.exists():
        log(f"🛑 CRITICAL FAILURE: UI script not found at {ui_script}")
        sys.exit(1)

    core_script = str(core_script)
    ui_script = str(ui_script)

    def get_host_guid():
        """Generates a non-persistent, 64-bit session identifier."""
        return os.urandom(8).hex().upper()

    session_guid = get_host_guid()
    log(f"Session Identity established (Randomized): {session_guid}")
    
    # Clone the current environment and inject the session GUID.
    child_env = os.environ.copy()
    child_env["OPEN_AIR_INSTANCE_GUID"] = session_guid
    # ⚡ CRITICAL: Ensure the project root is in the child's PYTHONPATH.
    child_env["PYTHONPATH"] = os.pathsep.join([str(project_root), child_env.get("PYTHONPATH", "")])

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
        sig_name = "SIGINT" if sig == signal.SIGINT else "SIGTERM"
        log(f"🛑 {sig_name} received. Initiating graceful shutdown...")
        shutdown_requested[0] = True

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

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

    def interpret_exit_code(code):
        """Returns a human-readable description of process exit reasons."""
        if code == 0: return "The service closed gracefully."
        if code == -11: return "The service crashed due to a critical memory error (Segmentation Fault)."
        if code == -15: return "The service was stopped by a termination request."
        if code == -9: return "The service was forcefully killed by the system."
        if code == 1: return "The service failed to start or encountered a generic error."
        return f"The service exited with an unhandled status code: {code}"

    # --- Monitoring Loop ---
    while not shutdown_requested[0]:
        time.sleep(0.5) # Throttle loop to minimize CPU impact.
        
        # Check Core partition liveness.
        if p_core.poll() is not None:
            code = p_core.returncode
            desc = interpret_exit_code(code)
            if is_mission_critical and not shutdown_requested[0]:
                log(f"⚠️ The Core engine has stopped ({desc}). Restarting automatically...")
                time.sleep(1.0) # ⚡ OPTIMIZATION: Throttled restart backoff
                p_core = subprocess.Popen([python_executable, core_script], 
                                            env=core_env)
                processes[0] = p_core
            else:
                log(f"🛑 The Core engine has exited ({desc}). Shutting down the entire system.")
                break
        
        # Check UI partition liveness.
        if p_ui.poll() is not None:
            code = p_ui.returncode
            desc = interpret_exit_code(code)
            if is_mission_critical and not shutdown_requested[0]:
                log(f"⚠️ The UI has stopped ({desc}). Restarting automatically...")
                time.sleep(1.0) # ⚡ OPTIMIZATION: Throttled restart backoff
                p_ui = subprocess.Popen([python_executable, ui_script], 
                                            env=ui_env)
                processes[1] = p_ui
            else:
                if code == 0:
                    log("👋 The User Interface was closed normally. System complete.")
                else:
                    log(f"🚨 The User Interface has exited unexpectedly ({desc}).")
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
    
    # --- FINAL LOGGING FLUSH ---
    from oaLogging.Core.logger import shutdown_logging
    shutdown_logging()
    
    log("Supervisor shutdown complete. Goodbye.")

if __name__ == "__main__":
    main()