# OpenAir.py
# Author: Anthony Peter Kuzub
# Version: 20260323.1700.1
#
# Description: The Multi-Process Supervisor for the OPEN-AIR System.

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
    - Assumes the presence of 'oaComBroker/Core/open_air_core.py' and 
      'oaGuiManager/Managers/open_air_ui.py'.
"""

import sys
import os
import time
import subprocess
import pathlib
import signal
import psutil

# Ensure the root directory is in the search path for local module imports.
current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from oaLogging.Core.logger import initialize_logging, set_log_directory, SYSTEM_LOGGER as logger
from oaOchestration.Core.path_initializer import initialize_paths, DATA_LOGS_DIR, DATA_RUNNING_DIR
from oaConfiguration.FileReaders.config_reader import Config

def perform_preflight_checks():
    """
    Verifies system integrity before launching partitions.
    Checks for lingering processes and improper previous shutdowns.
    """
    logger.info("🔍 [SUPERVISOR] Performing pre-flight integrity checks...")
    
    # 1. Check for improper shutdown (Lock File)
    lock_file = DATA_RUNNING_DIR / "SYSTEM.lock"
    if lock_file.exists():
        logger.warning("⚠️ [INTEGRITY] Found leftover lock-file from previous session.")
        logger.warning("⚠️ [INTEGRITY] System was likely not destroyed properly.")
        try:
            lock_file.unlink()
            logger.info("🧹 [INTEGRITY] Stale lock-file cleared.")
        except Exception as e:
            logger.error(f"❌ [INTEGRITY] Failed to clear lock-file: {e}")
    else:
        logger.success("✅ [INTEGRITY] Previous session was destroyed properly.")

    # 2. Check for lingering child processes
    current_pid = os.getpid()
    zombies_found = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Skip ourselves
            if proc.info['pid'] == current_pid:
                continue
            
            cmdline = proc.info['cmdline']
            if cmdline and any(s in ' '.join(cmdline) for s in ["open_air_core.py", "open_air_ui.py"]):
                logger.warning(f"🕵️ [INTEGRITY] Found lingering process: {proc.info['name']} (PID: {proc.info['pid']})")
                proc.terminate()
                zombies_found = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if zombies_found:
        logger.info("🧹 [INTEGRITY] Lingering processes signaled to terminate.")
        time.sleep(1.0)
    else:
        logger.success("✅ [INTEGRITY] No lingering child processes detected.")

def create_system_lock():
    """Creates an ephemeral lock-file for the current session."""
    lock_file = DATA_RUNNING_DIR / "SYSTEM.lock"
    try:
        with open(lock_file, "w") as f:
            f.write(str(os.getpid()))
        logger.debug(f"🔒 [SUPERVISOR] System lock established (PID: {os.getpid()})")
    except Exception as e:
        logger.error(f"❌ [SUPERVISOR] Failed to create system lock: {e}")

def release_system_lock():
    """Removes the current session's lock-file."""
    lock_file = DATA_RUNNING_DIR / "SYSTEM.lock"
    if lock_file.exists():
        try:
            lock_file.unlink()
            logger.debug("🔓 [SUPERVISOR] System lock released.")
        except Exception as e:
            logger.error(f"❌ [SUPERVISOR] Failed to release system lock: {e}")

def main():
    """
    Executes the supervisor lifecycle: Setup -> Spawn -> Monitor -> Shutdown.
    """
    # Handle direct partition launching for developer convenience.
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "--core":
            from oaComBroker.Core import open_air_core as core_mod
            core_mod.main()
            return
        elif mode == "--ui":
            from oaGuiManager.Managers import open_air_ui as ui_mod
            ui_mod.main()
            return

    # --- Supervisor Setup ---
    initialize_paths()
    log_dir = DATA_LOGS_DIR
    set_log_directory(log_dir, partition="SUP")
    
    # ⚡ INTEGRITY: Verify previous session and establish current lock
    perform_preflight_checks()
    create_system_lock()
    
    app_config = Config.get_instance()
    is_mission_critical = app_config.MISSION_CRITICAL_MODE

    if LOCAL_DEBUG:
        logger.info(f"Launching OPEN-AIR Partitions... (Mission Critical: {is_mission_critical})")

    python_executable = sys.executable
    
    # Core Partition (Communication & Logic)
    core_script = os.path.join(current_dir, "oaComBroker", "Core", "open_air_core.py")
    if not os.path.exists(core_script):
        core_script = os.path.join(current_dir, "oaComBroker", "open_air_core.py")
        
    # UI Partition (Display & Interaction)
    ui_script = os.path.join(current_dir, "oaGuiManager", "Managers", "open_air_ui.py")
    if not os.path.exists(ui_script):
        ui_script = os.path.join(current_dir, "oaGuiManager", "open_air_ui.py")

    def get_host_guid():
        """Generates a non-persistent, 64-bit session identifier."""
        return os.urandom(8).hex().upper()

    session_guid = get_host_guid()
    if LOCAL_DEBUG:
        logger.debug(f"Session Identity established (Randomized): {session_guid}")
    
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
        if LOCAL_DEBUG:
            logger.info("Keyboard Interrupt (Signal). Initiating graceful shutdown...")
        shutdown_requested[0] = True

    signal.signal(signal.SIGINT, signal_handler)

    # 1. Launch UI Partition (Handles User Feedback/Splash Screen).
    if LOCAL_DEBUG: logger.debug("Spawning Partition B (UI)...")
    p_ui = subprocess.Popen([python_executable, ui_script], env=ui_env)
    processes.append(p_ui)
    
    # 2. Launch Core Partition (Handles Hardware/Logic).
    if LOCAL_DEBUG: logger.debug("Spawning Partition A (Core)...")
    p_core = subprocess.Popen([python_executable, core_script], env=core_env)
    processes.insert(0, p_core)
    
    if LOCAL_DEBUG:
        logger.success("System Running. Monitoring child processes...")

    # --- Monitoring Loop ---
    while not shutdown_requested[0]:
        time.sleep(0.5) 
        
        # Check Core partition liveness.
        if p_core.poll() is not None:
            if is_mission_critical and not shutdown_requested[0]:
                logger.error(f"Core died (Code {p_core.returncode}). Restarting in 1s...")
                time.sleep(1.0) 
                p_core = subprocess.Popen([python_executable, core_script], env=core_env)
                processes[0] = p_core
            else:
                if LOCAL_DEBUG: logger.info(f"Core exited (Code {p_core.returncode}). Shutting down.")
                break
        
        # Check UI partition liveness.
        if p_ui.poll() is not None:
            if is_mission_critical and not shutdown_requested[0]:
                logger.warning(f"UI exited (Code {p_ui.returncode}). Restarting in 1s...")
                time.sleep(1.0) 
                p_ui = subprocess.Popen([python_executable, ui_script], env=ui_env)
                processes[1] = p_ui
            else:
                if LOCAL_DEBUG: logger.info(f"UI exited (Code {p_ui.returncode}). System complete.")
                break

    # --- Finalization and Cleanup ---
    if LOCAL_DEBUG: logger.debug("Terminating child processes...")
    for p in processes:
        if p and p.poll() is None:
            p.terminate()
            start_wait = time.time()
            while p.poll() is None and (time.time() - start_wait) < 2:
                time.sleep(0.1)
            
            if p.poll() is None:
                p.kill()
                p.wait()
    
    # ⚡ INTEGRITY: Final step is to release the session lock
    release_system_lock()

    if LOCAL_DEBUG:
        logger.success("Supervisor shutdown complete. Goodbye.")

if __name__ == "__main__":
    main()
