# oaSupervisor/Workers/partition_lifecycle.py
#
# Spawn / monitor / shutdown of the Core, UI and (optional) Web partitions.
# The supervisor's monitoring loop lives here too. Each partition's restart
# policy depends on `is_mission_critical`:
#   - Core / UI exit → restart if mission-critical, else shut the system down.
#   - Web exit       → restart if mission-critical, else leave it down
#                      (Web is auxiliary and never forces a full shutdown).

import signal
import subprocess
import sys
import time


def interpret_exit_code(code):
    """Human-readable description of common subprocess exit reasons."""
    if code == 0:   return "The service closed gracefully."
    if code == -11: return "The service crashed due to a critical memory error (Segmentation Fault)."
    if code == -15: return "The service was stopped by a termination request."
    if code == -9:  return "The service was forcefully killed by the system."
    if code == 1:   return "The service failed to start or encountered a generic error."
    return f"The service exited with an unhandled status code: {code}"


def install_signal_handlers(log):
    """Install SIGINT/SIGTERM handlers. Returns a [bool] flag the caller polls."""
    shutdown_requested = [False]

    def handler(sig, _frame):
        sig_name = "SIGINT" if sig == signal.SIGINT else "SIGTERM"
        log(f"🛑 {sig_name} received. Initiating graceful shutdown...")
        shutdown_requested[0] = True

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
    return shutdown_requested


def spawn_partitions(python_exe, scripts, envs, log):
    """Spawn UI → Core → (optional) Web. Returns dict of {p_core, p_ui, p_web, processes}."""
    core_script, ui_script, web_script = scripts
    child_env, core_env, ui_env = envs

    log("Spawning Partition B (UI)...")
    p_ui = subprocess.Popen([python_exe, ui_script], env=ui_env)

    log("Spawning Partition A (Core)...")
    p_core = subprocess.Popen([python_exe, core_script], env=core_env)

    # processes[0]=core, processes[1]=ui (used by monitoring loop to restart in place).
    processes = [p_core, p_ui]

    p_web = None
    if web_script:
        log("Spawning Web Interface (http://localhost:8000)...")
        p_web = subprocess.Popen([python_exe, web_script], env=child_env)
        processes.append(p_web)

    return {"p_core": p_core, "p_ui": p_ui, "p_web": p_web, "processes": processes}


def _restart_or_shutdown(name, exited, restart_args, restart_env, *,
                        is_mission_critical, shutdown_requested, log, processes, index):
    """Common restart-or-shutdown decision for Core/UI. Returns the live Popen (new or restarted)."""
    code = exited.returncode
    desc = interpret_exit_code(code)
    if is_mission_critical and not shutdown_requested[0]:
        log(f"⚠️ {name} has stopped ({desc}). Restarting automatically...")
        time.sleep(1.0)
        new_p = subprocess.Popen(restart_args, env=restart_env)
        processes[index] = new_p
        return new_p
    if name.startswith("The User Interface") and code == 0:
        log("👋 The User Interface was closed normally. System complete.")
    else:
        log(f"🛑 {name} has exited ({desc}). Shutting down the entire system.")
    shutdown_requested[0] = True
    return exited


def monitor_processes(state, scripts, envs, *, python_exe,
                      is_mission_critical, shutdown_requested, log):
    """Monitor Core/UI/Web liveness until a shutdown is requested."""
    core_script, ui_script, web_script = scripts
    child_env, core_env, ui_env = envs
    p_core, p_ui, p_web = state["p_core"], state["p_ui"], state["p_web"]
    processes = state["processes"]

    while not shutdown_requested[0]:
        time.sleep(0.5)  # Throttle to minimise CPU.

        if p_core.poll() is not None:
            p_core = _restart_or_shutdown(
                "The Core engine", p_core,
                [python_exe, core_script], core_env,
                is_mission_critical=is_mission_critical,
                shutdown_requested=shutdown_requested,
                log=log, processes=processes, index=0)
            if shutdown_requested[0]: break

        if p_ui.poll() is not None:
            p_ui = _restart_or_shutdown(
                "The User Interface", p_ui,
                [python_exe, ui_script], ui_env,
                is_mission_critical=is_mission_critical,
                shutdown_requested=shutdown_requested,
                log=log, processes=processes, index=1)
            if shutdown_requested[0]: break

        # Web is auxiliary — its exit NEVER forces a system shutdown.
        if p_web is not None and p_web.poll() is not None:
            code = p_web.returncode
            desc = interpret_exit_code(code)
            if is_mission_critical and not shutdown_requested[0]:
                log(f"⚠️ The Web Interface has stopped ({desc}). Restarting automatically...")
                time.sleep(1.0)
                p_web = subprocess.Popen([python_exe, web_script], env=child_env)
                processes[2] = p_web
            else:
                log(f"ℹ️ The Web Interface has exited ({desc}). Core system continues running.")
                p_web = None  # Stop polling.


def shutdown_processes(processes, log):
    """Terminate (then kill, if necessary) all child processes."""
    log("Terminating child processes...")
    for p in processes:
        if p and p.poll() is None:
            p.terminate()
            start = time.time()
            while p.poll() is None and (time.time() - start) < 2:
                time.sleep(0.1)
            if p.poll() is None:
                p.kill()
                p.wait()
