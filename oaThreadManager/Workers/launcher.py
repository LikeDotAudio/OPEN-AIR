# Workers/launcher.py
# Author: Anthony Peter Kuzub
# Version: 20260318.Modular.2
#
# Description: This file contains the function to launch and initialize all the application's managers.

import os
import threading
import pathlib
import sys
import importlib
import importlib.util

# Ensure the root directory is in the search path for local module imports.
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from oaLogging.Managers.log_filter_engine import initialize_filter_engine
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config
app_constants = Config.get_instance()

# --- Core/Mandatory Imports Only ---
from oaComMQTT.Entry import MqttConnectionManager, MqttSubscriberRouter, MqttManager
from oaComBroker.Entry import ProtocolRouter

def _load_protocol_manager(module_path, class_name, **kwargs):
    """Dynamically loads and instantiates a protocol manager if enabled."""
    spec = importlib.util.find_spec(module_path)
    if spec is None:
        logger.error(f"❌ Module {module_path} not found.")
        return None
    
    module = importlib.import_module(module_path)
    if not hasattr(module, class_name):
        logger.error(f"❌ Class {class_name} not found in module {module_path}.")
        return None
        
    manager_class = getattr(module, class_name)
    return manager_class(**kwargs)

def launch_core_managers(state_cache_manager, mqtt_connection_manager):
    """
    Initializes and launches all the CORE application managers (Headless).
    """
    if LOCAL_DEBUG: logger.debug("🚀⚙️🔗 [LAUNCHER] Beginning CORE manager launch sequence...")

    # --- 1. Initialization Phase ---
    if LOCAL_DEBUG: logger.debug("🚀⚙️🔗 [LAUNCHER] Initializing core instances...")
    
    subscriber_router = MqttSubscriberRouter()
    protocol_router = ProtocolRouter.get_instance()
    
    # Initialize the log filter engine to enable dynamic log filtering via MQTT.
    initialize_filter_engine(mqtt_router=subscriber_router, logger_reconfigurator_callable=initialize_logging)
    
    # Core Infrastructure
    splinker_entry_path = "oaSplinker.Entry"
    if importlib.util.find_spec(splinker_entry_path):
        splinker_entry = importlib.import_module(splinker_entry_path)
        splinker_manager = splinker_entry.get_broker(state_cache_manager, mqtt_connection_manager)
    else:
        logger.critical("❌ Critical module missing: oaSplinker.Entry")
        return None
    
    mqtt_manager = MqttManager(subscriber_router=subscriber_router, mqtt_client=mqtt_connection_manager, state_cache_manager=state_cache_manager)

    # --- Dynamic Protocol Injection ---
    if LOCAL_DEBUG: logger.debug("🚀⚙️🔗 [LAUNCHER] Injecting dynamic protocols...")

    aes70_manager = None
    # 📻🔌🛑 [DISABLED] AES70 Feature is currently suspended for re-architecture.
    #     aes70_manager = _load_protocol_manager(
    #         "oaComAES70.Entry", "AES70Manager",
    #         state_cache=state_cache_manager, run_bridge=True
    #     )

    osc_manager = _load_protocol_manager(
        "oaComOSC.Entry", "get_manager",
        state_cache_manager=state_cache_manager, mqtt_connection_manager=mqtt_connection_manager, run_bridge=True
    )

    snmp_manager = None
    if getattr(app_constants, "SCAN_SNMP", False):
        snmp_manager = _load_protocol_manager(
            "oaComSNMP.Entry", "get_manager",
            state_cache_manager=state_cache_manager, 
            mqtt_connection_manager=mqtt_connection_manager, 
            subscriber_router=subscriber_router,
            run_bridge=True
        )
        if snmp_manager:
            snmp_manager.start()

    # MIDI bridge is always on for core
    midi_manager = _load_protocol_manager(
        "oaComMidi.Entry", "get_manager",
        state_cache_manager=state_cache_manager, run_bridge=True
    )

    # REST API for external control
    rest_manager = _load_protocol_manager(
        "oaComREST.Entry", "get_manager",
        state_cache_manager=state_cache_manager, protocol_router=protocol_router
    )
    
    # Fleet & Yak (Loaded dynamically to avoid import loops)
    visa_entry_path = "oaComVisa.Entry"
    if importlib.util.find_spec(visa_entry_path):
        visa_entry = importlib.import_module(visa_entry_path)
        # FleetOrchestrator might be in visa_fleet, checking DiscoveryOrchestrator for now or visa_manager
        # Based on Entry.py it has DiscoveryOrchestrator and VisaManagerOrchestrator
        # Let's use get_discovery_orchestrator
        STATE_VISA_FLEET_manager = visa_entry.get_discovery_orchestrator(
            manager_ref=None, # Needs a reference to the main app if used for callbacks
            aes70_manager=aes70_manager
        )
    else:
        logger.critical("❌ Critical module missing: oaComVisa.Entry")
        return None
    
    yak_entry_path = "oaTranslator.Entry"
    if importlib.util.find_spec(yak_entry_path):
        yak_entry = importlib.import_module(yak_entry_path)
        # yak_entry exports YakTranslator
        yak_translator = yak_entry.YakTranslator(mqtt_connection_manager=mqtt_connection_manager, subscriber_router=subscriber_router)
        # yak_rx was in Methods, maybe not in Entry. Let's load it from Methods.
        yak_rx_module = importlib.import_module("oaTranslator.Methods.yak_rx")
        yak_rx_manager = yak_rx_module.YakRxManager(
            mqtt_connection_manager=mqtt_connection_manager, 
            subscriber_router=subscriber_router, 
            yak_translator=yak_translator, 
            state_cache_manager=state_cache_manager
        )
    else:
        logger.critical("❌ Critical module missing: oaTranslator.Entry")
        return None
    
    watchdog_entry_path = "oaWatchdog.Entry"
    if importlib.util.find_spec(watchdog_entry_path):
        watchdog_entry = importlib.import_module(watchdog_entry_path)
        fleet_status_monitor = watchdog_entry.FleetStatusMonitor(state_mirror_engine=None, subscriber_router=subscriber_router)
    else:
        logger.critical("❌ Critical module missing: oaWatchdog.Entry")
        return None
    
    ptp_entry_path = "oaPTP.Entry"
    if importlib.util.find_spec(ptp_entry_path):
        ptp_entry = importlib.import_module(ptp_entry_path)
        ptp_manager = ptp_entry.get_manager(mqtt_connection_manager=mqtt_connection_manager, subscriber_router=subscriber_router)
    else:
        logger.critical("❌ Critical module missing: oaPTP.Entry")
        return None

    # --- 2. Linking Phase ---
    if LOCAL_DEBUG: logger.debug("🚀⚙️🔗 [LAUNCHER] Linking cross-dependent managers...")

    state_cache_manager.subscriber_router = subscriber_router
    state_cache_manager.state_mirror_engine = None # Core partition does not use StateMirrorEngine

    protocol_router.set_mqtt_manager(mqtt_connection_manager)
    protocol_router.set_splinker_manager(splinker_manager)
    
    if hasattr(protocol_router, "set_osc_manager") and osc_manager: protocol_router.set_osc_manager(osc_manager)
    if hasattr(protocol_router, "set_midi_manager") and midi_manager: protocol_router.set_midi_manager(midi_manager)
    
    def splinker_mqtt_wrapper(msg):
        splinker_manager.handle_mqtt_command(msg.topic, msg.payload)
    subscriber_router.subscribe_to_topic("OPEN-AIR/System/Control/Splinker/#", splinker_mqtt_wrapper)

    # --- 3. Start Phase ---
    if LOCAL_DEBUG: logger.debug("🚀⚙️🔗 [LAUNCHER] Starting all manager services...")

    if aes70_manager: aes70_manager.start()
    if osc_manager: osc_manager.start()
    if midi_manager: midi_manager.start()
    if rest_manager: rest_manager.start()
    
    if hasattr(STATE_VISA_FLEET_manager, "start"):
        STATE_VISA_FLEET_manager.start()
    elif hasattr(STATE_VISA_FLEET_manager, "scan_and_manage_fleet"):
        # DiscoveryOrchestrator uses scan_and_manage_fleet or worker thread
        pass 

    ptp_manager.start()
    protocol_router.start() # Start router threads last before network

    def start_network_services():
        """Explicitly initiates MQTT connection and background scans."""
        if LOCAL_DEBUG: logger.debug("🚀⚙️🔗 [LAUNCHER] Connecting CORE MQTT Client to broker and running scans...")
        
        mqtt_connection_manager.connect_to_broker(
            on_message_callback=state_cache_manager.handle_incoming_mqtt,
            subscriber_router=subscriber_router,
        )
        state_cache_manager.subscribe_to_all_topics()
        
        if hasattr(STATE_VISA_FLEET_manager, "trigger_scan"):
            scan_thread = threading.Thread(target=STATE_VISA_FLEET_manager.trigger_scan, daemon=True)
            scan_thread.start()
        elif hasattr(STATE_VISA_FLEET_manager, "scan_and_manage_fleet"):
            STATE_VISA_FLEET_manager.scan_and_manage_fleet()

    start_network_services()

    if LOCAL_DEBUG: logger.success("✅✅✅ [SUCCESS] All CORE managers have been successfully launched!")

    return {
        "mqtt_connection_manager": mqtt_connection_manager,
        "subscriber_router": subscriber_router,
        "state_mirror_engine": None,
        "aes70_manager": aes70_manager,
        "osc_manager": osc_manager,
        "snmp_manager": snmp_manager,
        "midi_manager": midi_manager,
        "rest_manager": rest_manager,
        "STATE_VISA_FLEET_manager": STATE_VISA_FLEET_manager,
        "yak_translator": yak_translator,
        "yak_rx_manager": yak_rx_manager,
        "fleet_status_monitor": fleet_status_monitor,
        "ptp_manager": ptp_manager,
        "mqtt_manager": mqtt_manager,
        "protocol_router": protocol_router,
        "start_network_services": start_network_services,
    }
