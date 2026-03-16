# managers/manager_launcher.py
#
# This file contains the function to launch and initialize all the application's managers.
# REFACTORED for Partitioned Architecture (Core Only) and Modular Dependency Injection.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20260315.Modular.1

import os
import inspect
import threading
import pathlib
import sys
import importlib

import importlib.util

# Ensure the root directory is in the search path for local module imports.
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from workers.logger.log_filter_engine import initialize_filter_engine
from loguru import logger

from managers.configini.config_reader import Config
app_constants = Config.get_instance()

# --- Core/Mandatory Imports Only ---
from workers.Command_Router.mqtt.mqtt_connection_manager import MqttConnectionManager
from workers.Command_Router.mqtt.mqtt_subscriber_router import MqttSubscriberRouter
from workers.Command_Router.Mqtt_Manager.mqtt_manager import MqttManager
from workers.Command_Router.protocol_router import ProtocolRouter

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
    # This must be called after the MQTT router and logger are set up.
    initialize_filter_engine(mqtt_router=subscriber_router, logger_reconfigurator_callable=initialize_logging)
    
    # Core Infrastructure
    splinker_module_path = "workers.Splinker.splinker_manager"
    if importlib.util.find_spec(splinker_module_path):
        splinker_module = importlib.import_module(splinker_module_path)
        splinker_manager = splinker_module.SplinkerManager.get_instance(state_cache_manager, mqtt_connection_manager)
    else:
        logger.critical("❌ Critical module missing: workers.Splinker.splinker_manager")
        return None
    
    mqtt_manager = MqttManager(subscriber_router=subscriber_router, mqtt_client=mqtt_connection_manager, state_cache_manager=state_cache_manager)

    # --- Dynamic Protocol Injection ---
    if LOCAL_DEBUG: logger.debug("🚀⚙️🔗 [LAUNCHER] Injecting dynamic protocols...")
    
    aes70_manager = None
    if getattr(app_constants, "SCAN_AES70", False):
        aes70_manager = _load_protocol_manager(
            "workers.Command_Router.AES70.aes70", "AES70Manager",
            state_cache_manager=state_cache_manager, run_bridge=True
        )

    osc_manager = None
    if getattr(app_constants, "SCAN_OSC", False):
        osc_manager = _load_protocol_manager(
            "workers.Command_Router.OSC.osc_manager", "OSCManager",
            state_cache_manager=state_cache_manager, mqtt_connection_manager=mqtt_connection_manager, run_bridge=True
        )

    snmp_manager = None
    if getattr(app_constants, "SCAN_SNMP", False):
        snmp_manager = _load_protocol_manager(
            "workers.Command_Router.SNMP.snmp_manager", "SNMPManager",
            state_cache_manager=state_cache_manager, mqtt_connection_manager=mqtt_connection_manager, run_bridge=True
        )

    # MIDI bridge is always on for core
    midi_manager = _load_protocol_manager(
        "workers.Command_Router.MIDI.midi_manager", "MidiManager",
        state_cache_manager=state_cache_manager, run_bridge=True
    )
    
    # Fleet & Yak (Loaded dynamically to avoid import loops)
    visa_fleet_module_path = "managers.Visa_Fleet_Manager.visa_fleet_manager"
    if importlib.util.find_spec(visa_fleet_module_path):
        visa_fleet_module = importlib.import_module(visa_fleet_module_path)
        STATE_VISA_FLEET_manager = visa_fleet_module.VisaFleetManager(
            mqtt_connection_manager=mqtt_connection_manager, 
            subscriber_router=subscriber_router, 
            aes70_manager=aes70_manager
        )
    else:
        logger.critical("❌ Critical module missing: managers.Visa_Fleet_Manager.visa_fleet_manager")
        return None
    
    yak_translator_module_path = "managers.yak.yak_translator"
    if importlib.util.find_spec(yak_translator_module_path):
        yak_translator_module = importlib.import_module(yak_translator_module_path)
        yak_translator = yak_translator_module.YakTranslator(mqtt_connection_manager=mqtt_connection_manager, subscriber_router=subscriber_router)
    else:
        logger.critical("❌ Critical module missing: managers.yak.yak_translator")
        return None
    
    yak_rx_module_path = "managers.yak.manager_yak_rx"
    if importlib.util.find_spec(yak_rx_module_path):
        yak_rx_module = importlib.import_module(yak_rx_module_path)
        yak_rx_manager = yak_rx_module.YakRxManager(
            mqtt_connection_manager=mqtt_connection_manager, 
            subscriber_router=subscriber_router, 
            yak_translator=yak_translator, 
            state_cache_manager=state_cache_manager
        )
    else:
        logger.critical("❌ Critical module missing: managers.yak.manager_yak_rx")
        return None
    
    fleet_status_module_path = "workers.monitoring.fleet_status_monitor"
    if importlib.util.find_spec(fleet_status_module_path):
        fleet_status_module = importlib.import_module(fleet_status_module_path)
        fleet_status_monitor = fleet_status_module.FleetStatusMonitor(state_mirror_engine=None, subscriber_router=subscriber_router)
    else:
        logger.critical("❌ Critical module missing: workers.monitoring.fleet_status_monitor")
        return None
    
    ptp_module_path = "managers.PTP.ptp_manager"
    if importlib.util.find_spec(ptp_module_path):
        ptp_module = importlib.import_module(ptp_module_path)
        ptp_manager = ptp_module.PtpManager(mqtt_connection_manager=mqtt_connection_manager, subscriber_router=subscriber_router)
    else:
        logger.critical("❌ Critical module missing: managers.PTP.ptp_manager")
        return None

    # --- 2. Linking Phase ---
    if LOCAL_DEBUG: logger.debug("🚀⚙️🔗 [LAUNCHER] Linking cross-dependent managers...")

    state_cache_manager.subscriber_router = subscriber_router
    state_cache_manager.state_mirror_engine = None # Core partition does not use StateMirrorEngine

    protocol_router.set_mqtt_manager(mqtt_connection_manager)
    protocol_router.set_splinker_manager(splinker_manager)
    
    if osc_manager: protocol_router.set_osc_manager(osc_manager)
    if midi_manager: protocol_router.set_midi_manager(midi_manager)
    if snmp_manager: protocol_router.set_snmp_manager(snmp_manager)
    
    def splinker_mqtt_wrapper(msg):
        splinker_manager.handle_mqtt_command(msg.topic, msg.payload)
    subscriber_router.subscribe_to_topic("OPEN-AIR/System/Control/Splinker/#", splinker_mqtt_wrapper)

    # --- 3. Start Phase ---
    if LOCAL_DEBUG: logger.debug("🚀⚙️🔗 [LAUNCHER] Starting all manager services...")

    if aes70_manager: aes70_manager.start()
    if osc_manager: osc_manager.start()
    if snmp_manager: snmp_manager.start()
    if midi_manager: midi_manager.start()
    
    STATE_VISA_FLEET_manager.start()
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
        
        scan_thread = threading.Thread(target=STATE_VISA_FLEET_manager.trigger_scan, daemon=True)
        scan_thread.start()

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
        "STATE_VISA_FLEET_manager": STATE_VISA_FLEET_manager,
        "yak_translator": yak_translator,
        "yak_rx_manager": yak_rx_manager,
        "fleet_status_monitor": fleet_status_monitor,
        "ptp_manager": ptp_manager,
        "mqtt_manager": mqtt_manager,
        "protocol_router": protocol_router,
        "start_network_services": start_network_services,
    }
