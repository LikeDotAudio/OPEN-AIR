"""
openair.py — Multi-process supervisor entry point for OPEN-AIR.

The supervisor's job is small and well-defined:
    1. (optional)   Direct-launch a single partition if asked (--core/--ui/--web).
    2. (setup)      Verify environment, validate scripts, build per-partition envs.
    3. (boot)       Initialise the Communication Protocol Manager (registration only).
    4. (spawn)      Launch UI → Core → Web as subprocesses.
    5. (monitor)    Watch their liveness and (in mission-critical mode) restart on crash.
    6. (shutdown)   Terminate children, stop protocols, flush logs, exit.

All real work lives in `oaSupervisor/` — this file is just orchestration.

Author: Anthony Peter Kuzub
"""

import pathlib
import re
import sys

project_root = pathlib.Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Core.logger import set_log_directory, shutdown_logging
from oaOchestration.Core.path_initializer import initialize_paths

from oaSupervisor.Methods.direct_launch import handle_direct_launch
from oaSupervisor.Methods.environment import (
    build_partition_environments,
    resolve_partition_scripts,
    verify_rust_pipeline,
)
from oaSupervisor.Workers.partition_lifecycle import (
    install_signal_handlers,
    monitor_processes,
    shutdown_processes,
    spawn_partitions,
)
from oaSupervisor.Workers.protocol_lifecycle import (
    initialize_protocol_manager,
    shutdown_protocol_manager,
)

_ANSI = re.compile(r'\x1B(?:[@-Z\-_]|\[[0-?]*[ -/]*[@-~])')


def log(message):
    """Supervisor-stamped console output (ANSI codes stripped)."""
    print(f"[SUPERVISOR] {_ANSI.sub('', str(message))}")


def main():
    # 1. Developer escape-hatch — direct-launch a single partition and exit.
    if handle_direct_launch(sys.argv, project_root, log):
        return

    # 2. Supervisor setup.
    _, data_dir = initialize_paths()
    set_log_directory(pathlib.Path(data_dir) / "oaDataLogs", partition="SUP")

    is_mission_critical = Config.get_instance().MISSION_CRITICAL_MODE
    log(f"Launching OPEN-AIR Partitions... (Mission Critical: {is_mission_critical})")

    verify_rust_pipeline(project_root, log)
    scripts = resolve_partition_scripts(project_root, log)
    _, child_env, core_env, ui_env = build_partition_environments(project_root, log)
    envs = (child_env, core_env, ui_env)
    shutdown_requested = install_signal_handlers(log)

    # 3. Centralised protocol registration (services start in the Core partition).
    initialize_protocol_manager(log)

    # 4. Spawn partitions and 5. monitor.
    state = spawn_partitions(sys.executable, scripts, envs, log)
    log("System Running. Monitoring child processes...")
    try:
        monitor_processes(state, scripts, envs,
                          python_exe=sys.executable,
                          is_mission_critical=is_mission_critical,
                          shutdown_requested=shutdown_requested,
                          log=log)
    finally:
        # 6. Shutdown (always runs — even on exceptions).
        shutdown_processes(state["processes"], log)
        shutdown_protocol_manager(log)
        shutdown_logging()
        log("Supervisor shutdown complete. Goodbye.")


if __name__ == "__main__":
    main()
