# Workers/launcher.py
#
# Launches and initializes all application managers. Orchestrates the 
# high-level linking phase and bootstrap sequence for the core partition.
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
# Version 20260330.1600.1

import os
import threading
import pathlib
import sys
import importlib
import importlib.util
from oaLogging.Core.logger import logger

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory
from oaLogging.Managers.log_filter_engine import initialize_filter_engine
from oaLogging.Methods.matrix_gate import matrix_log

from oaConfigurationManager.FileReaders.config_reader import Config
app_constants = Config.get_instance()

# --- Core/Mandatory Imports Only ---
from oaComProtocols.oaComMQTT.Entry import MqttConnectionManager, MqttSubscriberRouter, MqttManager
from oaComBroker.Entry import ProtocolRouter

class CriticalModuleMissingError(Exception): pass

def _load_protocol_manager(module_path, class_name, **kwargs):
    spec = importlib.util.find_spec(module_path)
    if spec is None:
        return None
    
    module = importlib.import_module(module_path)
    if not hasattr(module, class_name):
        return None
        
    manager_class = getattr(module, class_name)
    return manager_class(**kwargs)

def launch_core_managers(state_cache_manager, mqtt_connection_manager):
    matrix_log("core", "launcher", "launch_core_managers", "🚀⚙️🔗 [LAUNCHER] Beginning CORE manager launch sequence...", "DEBUG")

    subscriber_router = MqttSubscriberRouter()
    protocol_router = ProtocolRouter.get_instance()
    
    initialize_filter_engine(mqtt_router=subscriber_router, logger_reconfigurator_callable=initialize_logging)
    
    # Core Infrastructure
    splinker_entry_path = "oaSplinker.Entry"
    if importlib.util.find_spec(splinker_entry_path):
        splinker_entry = importlib.import_module(splinker_entry_path)
        splinker_manager = splinker_entry.get_broker(state_cache_manager, mqtt_connection_manager)
    else:
        raise CriticalModuleMissingError("❌ Critical module missing: oaSplinker.Entry")
    
    mqtt_manager = MqttManager(subscriber_router=subscriber_router, mqtt_client=mqtt_connection_manager, state_cache_manager=state_cache_manager)

    # --- Dynamic Protocol Injection ---
    matrix_log("core", "launcher", "launch_core_managers", "🚀⚙️🔗 [LAUNCHER] Injecting dynamic protocols...", "DEBUG")

    aes70_manager = None
    osc_manager = _load_protocol_manager(
        "oaComProtocols.oaComOSC.Entry", "get_manager",
        state_cache_manager=state_cache_manager, mqtt_connection_manager=mqtt_connection_manager, run_bridge=True
    )

    snmp_manager = None
    if getattr(app_constants, "SCAN_SNMP", False):
        snmp_manager = _load_protocol_manager(
            "oaComProtocols.oaComSNMP.Entry", "get_manager",
            state_cache_manager=state_cache_manager, 
            mqtt_connection_manager=mqtt_connection_manager, 
            subscriber_router=subscriber_router,
            run_bridge=True
        )
        if snmp_manager: snmp_manager.start()

    midi_manager = None
    if getattr(app_constants, "SCAN_MIDI", False):
        midi_manager = _load_protocol_manager(
            "oaComProtocols.oaComMidi.Entry", "get_manager",
            state_cache_manager=state_cache_manager, run_bridge=True
        )

    rest_manager = _load_protocol_manager(
        "oaComProtocols.oaComREST.Entry", "get_manager",
        state_cache_manager=state_cache_manager, protocol_router=protocol_router
    )
    if rest_manager: rest_manager.start()
    
    visa_entry_path = "oaComProtocols.oaComVisa.Entry"
    if importlib.util.find_spec(visa_entry_path):
        visa_entry = importlib.import_module(visa_entry_path)
        STATE_VISA_FLEET_manager = visa_entry.get_discovery_orchestrator(manager_ref=None, aes70_manager=aes70_manager)
    else:
        raise CriticalModuleMissingError("❌ Critical module missing: oaComProtocols.oaComVisa.Entry")
    
    yak_entry_path = "oaTranslator.Entry"
    if importlib.util.find_spec(yak_entry_path):
        yak_entry = importlib.import_module(yak_entry_path)
        yak_translator = yak_entry.YakTranslator(mqtt_connection_manager=mqtt_connection_manager, subscriber_router=subscriber_router)
        yak_receiver_module = importlib.import_module("oaTranslator.Methods.yak_receiver")
        yak_receiver_manager = yak_receiver_module.YakReceiverManager(mqtt_connection_manager=mqtt_connection_manager, subscriber_router=subscriber_router, yak_translator=yak_translator, state_cache_manager=state_cache_manager)
    else:
        raise CriticalModuleMissingError("❌ Critical module missing: oaTranslator.Entry")
    
    watchdog_entry_path = "oaWatchdog.Entry"
    if importlib.util.find_spec(watchdog_entry_path):
        watchdog_entry = importlib.import_module(watchdog_entry_path)
        fleet_status_monitor = watchdog_entry.FleetStatusMonitor(state_mirror_engine=None, subscriber_router=subscriber_router)
    else:
        raise CriticalModuleMissingError("❌ Critical module missing: oaWatchdog.Entry")
    
    ptp_entry_path = "oaPTP.Entry"
    ptp_manager = None
    if importlib.util.find_spec(ptp_entry_path):
        try:
            ptp_entry = importlib.import_module(ptp_entry_path)
            ptp_manager = ptp_entry.get_manager(mqtt_connection_manager=mqtt_connection_manager, subscriber_router=subscriber_router)
        except Exception as e:
            matrix_log("core", "launcher", "launch_core_managers", f"⚠️ [LAUNCHER] Failed to load PTP manager: {e}. System will continue without PTP support.", "WARNING")
    else:
        matrix_log("core", "launcher", "launch_core_managers", "⚠️ [LAUNCHER] oaPTP.Entry not found. System will continue without PTP support.", "WARNING")


    # SMPTE2138 Bridge (Internal Actions -> External st2138 Protobuf)
    smpte2138_entry_path = "oaComProtocols.oaComSMPTE2138.Entry"
    smpte2138_manager = None
    if importlib.util.find_spec(smpte2138_entry_path):
        smpte2138_entry = importlib.import_module(smpte2138_entry_path)
        smpte2138_manager = smpte2138_entry.start_bridge(mqtt_connection_manager, subscriber_router)
    else:
        matrix_log("core", "launcher", "launch_core_managers", "⚠️ SMPTE2138 Bridge module (oaComProtocols.oaComSMPTE2138) not found. Skipping.", "WARNING")

    # NMOS IS-07 Bridge
    from oaComBroker.Managers.nmos_manager import NmosManager
    nmos_manager = NmosManager(registrar_url=getattr(app_constants, "NMOS_REGISTRAR", "http://localhost:4000"))

    # --- 2. Linking Phase ---
    matrix_log("core", "launcher", "launch_core_managers", "🚀⚙️🔗 [LAUNCHER] Linking cross-dependent managers...", "DEBUG")

    state_cache_manager.subscriber_router = subscriber_router
    state_cache_manager.state_mirror_engine = None 

    protocol_router.set_mqtt_manager(mqtt_connection_manager)
    protocol_router.set_splinker_manager(splinker_manager)
    
    if hasattr(protocol_router, "set_osc_manager") and osc_manager: protocol_router.set_osc_manager(osc_manager)
    if hasattr(protocol_router, "set_midi_manager") and midi_manager: protocol_router.set_midi_manager(midi_manager)
    if hasattr(protocol_router, "set_snmp_manager") and snmp_manager: protocol_router.set_snmp_manager(snmp_manager)
    if hasattr(protocol_router, "set_nmos_manager") and nmos_manager: protocol_router.set_nmos_manager(nmos_manager)
    if hasattr(protocol_router, "set_smpte2138_manager") and smpte2138_manager: protocol_router.set_smpte2138_manager(smpte2138_manager)
    
    def splinker_mqtt_wrapper(message):
        splinker_manager.handle_mqtt_command(message.topic, message.payload)
    subscriber_router.subscribe_to_topic("OPEN-AIR/System/Control/Splinker/#", splinker_mqtt_wrapper)

    # --- 3. Start Phase ---
    matrix_log("core", "launcher", "launch_core_managers", "🚀⚙️🔗 [LAUNCHER] Starting all manager services...", "DEBUG")

    if aes70_manager: aes70_manager.start()
    if osc_manager: osc_manager.start()
    if midi_manager: midi_manager.start()
    if nmos_manager: nmos_manager.start()
    if rest_manager: rest_manager.start()
    if smpte2138_manager: smpte2138_manager.start()
    
    if hasattr(STATE_VISA_FLEET_manager, "start"): STATE_VISA_FLEET_manager.start()
    if ptp_manager: ptp_manager.start()
    protocol_router.start() 

    def start_network_services():
        matrix_log("core", "launcher", "start_network_services", "🚀⚙️🔗 [LAUNCHER] Connecting CORE MQTT Client to broker and running scans...", "DEBUG")
        mqtt_connection_manager.connect_to_broker(on_message_callback=state_cache_manager.handle_incoming_mqtt, subscriber_router=subscriber_router)
        state_cache_manager.subscribe_to_all_topics()
        
        if hasattr(STATE_VISA_FLEET_manager, "trigger_scan"):
            scan_thread = threading.Thread(target=STATE_VISA_FLEET_manager.trigger_scan, daemon=True)
            scan_thread.start()
        elif hasattr(STATE_VISA_FLEET_manager, "scan_and_manage_fleet"):
            STATE_VISA_FLEET_manager.scan_and_manage_fleet()

    # Launch network services in the background to avoid blocking the main core thread
    threading.Thread(target=start_network_services, daemon=True, name="Launcher-NetworkBoot").start()

    matrix_log("core", "launcher", "launch_core_managers", "✅✅✅ [SUCCESS] All CORE managers have been successfully launched!", "SUCCESS")

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
        "yak_receiver_manager": yak_receiver_manager,
        "fleet_status_monitor": fleet_status_monitor,
        "ptp_manager": ptp_manager,
        "mqtt_manager": mqtt_manager,
        "nmos_manager": nmos_manager,
        "protocol_router": protocol_router,
        "smpte2138_manager": smpte2138_manager,
        "start_network_services": start_network_services,
    }
