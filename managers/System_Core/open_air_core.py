#!/usr/bin/env python3
# managers/System_Core/open_air_core.py
#
# Safety-Critical Core Partition for OPEN-AIR.
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
# Version 20260314.120000.REV01

"""
open_air_core.py - Safety-Critical Core Partition for OPEN-AIR.

Purpose:
    Serves as the central orchestration point for the OPEN-AIR hardware-facing
    logic. It is responsible for initializing system paths, logging, 
    configuration, and launching the core managers that handle MQTT 
    communication and state synchronization.

Primary Responsibilities:
    - Execute system initialization and high-priority path resolution.
    - Manage the hardware watchdog to ensure system liveness (heartbeat).
    - Orchestrate the lifecycle of MQTT and State Cache managers.
    - Implement a graceful shutdown sequence for all background services.

Assumptions and Constraints:
    - Assumes a POSIX-compliant environment for file and path handling.
    - Requires network access for MQTT communication if configured.
    - Expects 'config.ini' to be present and structurally valid.
    - Designed to run as a headless, statically allocated service.
    - Requires write permissions for the log and data directories.
"""

import sys
import os
import time
import pathlib

# Ensure the root directory is in the search path for local module imports.
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from managers.configini.config_reader import Config
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from workers.initialization.path_initializer import initialize_paths
from managers.configini.console_encoder import configure_console_encoding
import workers.watchdog.watchdog as watchdog
from workers.Command_Router.mqtt.mqtt_connection import MqttConnectionManager
from workers.Command_Router.State_Cache.state_cache import StateRegistry
from managers.launcher import launch_core_managers
from workers.Command_Router.mqtt.mqtt_publisher_service import shutdown_publisher_worker

# LOCAL_DEBUG: Toggles verbose tracing for the core boot sequence.
LOCAL_DEBUG = True

def main():
    """
    Orchestrates the startup, execution, and shutdown of the OPEN-AIR core.

    Lead with action: Initializes the core environment, starts the system
    watchdog, and launches the network-facing managers. Once operational,
    it enters a high-priority loop that services the watchdog.

    Inputs:
        None.

    Outputs:
        None. Process terminates on signal or critical failure.

    Side Effects and Thread-Safety:
        - Modifies the global 'sys.path' for the process.
        - Spawns multiple background threads for MQTT and Heartbeat.
        - Performs periodic I/O (filesystem/network) during the main loop.
        - Not thread-safe or reentrant; must be called as the main entry point.
    """
    # 1. --- Environment Initialization ---
    GLOBAL_PROJECT_ROOT, data_dir = initialize_paths()
    log_dir = pathlib.Path(data_dir) / "debug"
    
    # Establish a dedicated log partition to isolate core-level events.
    set_log_directory(log_dir, partition="CORE")
    configure_console_encoding()
    
    app_constants = Config.get_instance()
    
    if LOCAL_DEBUG:
        logger.debug("⚡🛡️⚙️ [CORE] Starting OpenAir Core Service...")

    # 2. --- Liveness Monitoring ---
    # The heartbeat thread ensures the system can be reset by hardware if the
    # software becomes unresponsive.
    watchdog.start_heartbeat(app_constants)
    
    # 3. --- Core Manager Lifecycle ---
    mqtt_connection_manager = MqttConnectionManager()
    state_cache_manager = StateRegistry(mqtt_connection_manager)
    
    # launch_core_managers returns a registry of active services.
    managers = launch_core_managers(state_cache_manager, mqtt_connection_manager)
    
    if not managers:
        logger.error("⚡🛡️⚙️ [CORE] CRITICAL: Manager launch failed. "
                     "Core partition aborting.")
        return

    # 4. --- Network Service Activation ---
    start_network_services = managers.get("start_network_services")
    if start_network_services:
        start_network_services()

    if LOCAL_DEBUG:
        logger.success("✅ [SUCCESS] CORE: Service Operational. Watchdog Active.")

    # 5. --- Primary Execution Loop ---
    try:
        while True:
            # Continually "pet" the watchdog to confirm process health.
            watchdog.kick_watchdog()
            # Sleep yields CPU to other processes while maintaining responsiveness.
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        if LOCAL_DEBUG:
            logger.debug("🛑 [CORE] Keyboard interrupt. Stopping...")
    except Exception as e:
        logger.exception("⚡ [CORE] CRITICAL: Unhandled exception in loop.")
    finally:
        # 6. --- Graceful Finalization ---
        if LOCAL_DEBUG:
            logger.debug("🔌 [CORE] Initiating teardown sequence...")
        
        # Stop all registered managers to ensure clean socket/thread closure.
        if managers:
            for name, manager in managers.items():
                if manager and hasattr(manager, "stop") and callable(manager.stop):
                    if LOCAL_DEBUG:
                        logger.debug(f"🔌 [CORE] Stopping '{name}'...")
                    try:
                        manager.stop()
                    except Exception as shutdown_err:
                        # Silently skip failed shutdowns during finalization.
                        pass
                    
        if state_cache_manager:
            state_cache_manager.shutdown()
            
        # Ensure the MQTT publisher thread is properly joined.
        shutdown_publisher_worker()
        
        if LOCAL_DEBUG:
            logger.success("👋 [SUCCESS] CORE: Shutdown sequence complete.")

if __name__ == "__main__":
    main()
