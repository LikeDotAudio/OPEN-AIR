import pathlib
import os
import sys
import threading
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# oaComBroker/Core/open_air_core.py
#
# Safety-Critical Core Partition for the Communication Broker.
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
# Version 20260328.1630.1
#
# Description:
# This module serves as the central orchestration point for the OPEN-AIR 
# hardware-facing logic. It initializes system paths, logging, configuration, 
# and launches the core managers for MQTT and state synchronization.
#
# Partitioned Architecture (Core vs UI):
# This is the 'Core' partition. It is designed to run headless and statically 
# allocated, providing the foundational services required for communication.
#
# Constraints & Dependencies:
# - Assumes a POSIX-compliant environment.
# - Requires network access for MQTT.
# - Depends on 'config.ini' presence.

import time

# Ensure the root directory is in the search path for local module imports.
from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Core.logger import initialize_logging, set_log_directory, CORE_LOGGER
from loguru import logger

LOCAL_DEBUG = False

from oaOchestration.Core.path_initializer import initialize_paths, DATA_LOGS_DIR
from oaConfigurationManager.Methods.console_encoder import configure_console_encoding
import oaWatchdog.Managers.watchdog as watchdog
from oaComProtocols.oaComMQTT.Managers.mqtt_connection import MqttConnectionManager
from oaStateCache.Core.state_cache import StateRegistry
from oaComBroker.Managers.Failover.Manager import FailoverManager
from oaComProtocols.oaComMQTT.Core.mqtt_publisher_service import shutdown_publisher_worker
# LOCAL_DEBUG: Toggles verbose tracing for the core boot sequence.

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
    # ⚡ CIRCULAR IMPORT PROTECTION: Import launcher here to break the loop with oaComBroker.Entry
    from oaThreadManager.Workers.launcher import launch_core_managers

    # 1. --- Environment Initialization ---
    initialize_paths()
    log_dir = DATA_LOGS_DIR
    
    # Establish a dedicated log partition to isolate core-level events.
    set_log_directory(log_dir, partition="CORE")
    configure_console_encoding()
    
    app_constants = Config.get_instance()
    
    if LOCAL_DEBUG:
        matrix_log("comms", "broker", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "Starting OpenAir Core Service...", "DEBUG")

    # 2. --- Liveness Monitoring ---
    # The heartbeat thread ensures the system can be reset by hardware if the
    # software becomes unresponsive.
    watchdog.start_heartbeat(app_constants)

    # ⚡ V3.1.29 GRACEFUL SHUTDOWN: Use an event instead of raising an interrupt 
    # to allow the main thread to finish its current work and enter cleanup safely.
    import signal
    shutdown_event = threading.Event()
    def handle_sigterm(signum, frame):
        if LOCAL_DEBUG:
            matrix_log("comms", "broker", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "SIGTERM received. Signaling graceful stop...", "DEBUG")
        shutdown_event.set()
    
    signal.signal(signal.SIGTERM, handle_sigterm)
    
    # 3. --- Core Manager Lifecycle ---
    mqtt_connection_manager = MqttConnectionManager()
    state_cache_manager = StateRegistry(mqtt_connection_manager)

    from oaComBroker.Core.protocol_router.manager import ProtocolRouter
    router = ProtocolRouter.get_instance()
    router.set_state_cache(state_cache_manager)
    # launch_core_managers returns a registry of active services.
    managers = launch_core_managers(state_cache_manager, mqtt_connection_manager)
    
    if not managers:
        CORE_LOGGER.error("CRITICAL: Manager launch failed. Core partition aborting.")
        return

    # 4. --- Network Service Activation ---
    # NOTE: start_network_services() is already called inside launch_core_managers()
    # No need to call it again here.

    # 4.5 --- High Availability Failover ---
    failover_mgr = FailoverManager(ProtocolRouter.get_instance(), mqtt_connection_manager)
    failover_mgr.start()

    if LOCAL_DEBUG:
        matrix_log("comms", "broker", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "CORE: Service Operational. Watchdog Active.", "SUCCESS")

    # 5. --- Primary Execution Loop ---
    try:
        while not shutdown_event.is_set():
            # Continually "pet" the watchdog to confirm process health.
            watchdog.kick_watchdog()
            # Sleep yields CPU to other processes while maintaining responsiveness.
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        if LOCAL_DEBUG:
            matrix_log("comms", "broker", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "Keyboard interrupt. Stopping...", "DEBUG")
    except Exception:
        CORE_LOGGER.exception("CRITICAL: Unhandled exception in loop.")
    finally:
        # 6. --- Graceful Finalization ---
        if LOCAL_DEBUG:
            matrix_log("comms", "broker", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "Initiating teardown sequence...", "DEBUG")
        
        # ⚡ V3.1.29 ORDER OF OPERATIONS: Shutdown the router FIRST to clear observers
        # and prevent 'main thread not in main loop' errors from UI components.
        if router:
            try:
                router.shutdown()
            except Exception as e:
                CORE_LOGGER.error(f"Error during router shutdown: {e}")

        # Stop all registered managers to ensure clean socket/thread closure.
        if managers:
            for name, manager in managers.items():
                if manager and hasattr(manager, "stop") and callable(manager.stop):
                    if LOCAL_DEBUG:
                        matrix_log("comms", "broker", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Stopping '{name}'...", "DEBUG")
                    try:
                        manager.stop()
                    except Exception:
                        # Silently skip failed shutdowns during finalization.
                        pass
                    
        if state_cache_manager:
            state_cache_manager.shutdown()
            
        # Ensure the MQTT publisher thread is properly joined.
        shutdown_publisher_worker()

        # --- FINAL LOGGING FLUSH ---
        from oaLogging.Core.logger import shutdown_logging
        shutdown_logging()
        
        if LOCAL_DEBUG:
            matrix_log("comms", "broker", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "CORE: Shutdown sequence complete.", "SUCCESS")

if __name__ == "__main__":
    main()