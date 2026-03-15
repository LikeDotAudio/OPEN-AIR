# managers/manager_launcher.py
#
# This file contains the function to launch and initialize all the application's managers.
# REFACTORED for Partitioned Architecture (Core Only).
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
# Version 20260221.Partition.1

import os
import inspect
import threading
import pathlib
import sys

# Ensure the root directory is in the search path for local module imports.
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

# --- MQTT and Proxy Imports ---
from workers.Command_Router.mqtt.mqtt_connection_manager import MqttConnectionManager
from workers.Command_Router.mqtt.mqtt_subscriber_router import MqttSubscriberRouter
from managers.Visa_Fleet_Manager.visa_fleet_manager import (
    VisaFleetManager,
)
from workers.Command_Router.AES70.aes70 import AES70Manager
from workers.Command_Router.OSC.osc_manager import OSCManager
from workers.Command_Router.SNMP.snmp_manager import SNMPManager
from workers.Command_Router.MIDI.midi_manager import MidiManager
from managers.yak.yak_translator import YakTranslator
from managers.yak.manager_yak_rx import YakRxManager
from workers.monitoring.fleet_status_monitor import (
    FleetStatusMonitor,
)
from managers.PTP.ptp_manager import PtpManager
from workers.Command_Router.Mqtt_Manager.mqtt_manager import MqttManager
from workers.Splinker.splinker_manager import SplinkerManager
from workers.Command_Router.protocol_router import ProtocolRouter


def launch_core_managers(state_cache_manager, mqtt_connection_manager):
    """
    Initializes and launches all the CORE application managers (Headless).
    """
    if LOCAL_DEBUG: logger.debug("🚀⚙️🔗 [LAUNCHER] Beginning CORE manager launch sequence...")

    # --- 1. Initialization Phase ---
    # Instantiate all managers first.
    if LOCAL_DEBUG: logger.debug("🚀⚙️🔗 [LAUNCHER] Initializing all manager instances...")
    
    subscriber_router = MqttSubscriberRouter()
    protocol_router = ProtocolRouter.get_instance()
    splinker_manager = SplinkerManager.get_instance(state_cache_manager, mqtt_connection_manager)
    
    aes70_manager = AES70Manager(state_cache_manager=state_cache_manager, run_bridge=app_constants.SCAN_AES70) if app_constants.SCAN_AES70 else None
    osc_manager = OSCManager(state_cache_manager=state_cache_manager, mqtt_connection_manager=mqtt_connection_manager, run_bridge=app_constants.SCAN_OSC) if app_constants.SCAN_OSC else None
    snmp_manager = SNMPManager(state_cache_manager=state_cache_manager, mqtt_connection_manager=mqtt_connection_manager, run_bridge=app_constants.SCAN_SNMP) if app_constants.SCAN_SNMP else None
    midi_manager = MidiManager(state_cache_manager=state_cache_manager, run_bridge=True) # MIDI bridge is always on
    
    STATE_VISA_FLEET_manager = VisaFleetManager(mqtt_connection_manager=mqtt_connection_manager, subscriber_router=subscriber_router, aes70_manager=aes70_manager)
    yak_translator = YakTranslator(mqtt_connection_manager=mqtt_connection_manager, subscriber_router=subscriber_router)
    yak_rx_manager = YakRxManager(mqtt_connection_manager=mqtt_connection_manager, subscriber_router=subscriber_router, yak_translator=yak_translator, state_cache_manager=state_cache_manager)
    fleet_status_monitor = FleetStatusMonitor(state_mirror_engine=None, subscriber_router=subscriber_router)
    ptp_manager = PtpManager(mqtt_connection_manager=mqtt_connection_manager, subscriber_router=subscriber_router)
    mqtt_manager = MqttManager(subscriber_router=subscriber_router, mqtt_client=mqtt_connection_manager, state_cache_manager=state_cache_manager)

    # --- 2. Linking Phase ---
    # Link all necessary components to the central router and each other.
    if LOCAL_DEBUG: logger.debug("🚀⚙️🔗 [LAUNCHER] Linking cross-dependent managers...")

    state_cache_manager.subscriber_router = subscriber_router
    state_cache_manager.state_mirror_engine = None # Core partition does not use StateMirrorEngine

    protocol_router.set_mqtt_manager(mqtt_connection_manager)
    protocol_router.set_splinker_manager(splinker_manager)
    protocol_router.set_osc_manager(osc_manager)
    protocol_router.set_midi_manager(midi_manager)
    protocol_router.set_snmp_manager(snmp_manager)
    
    def splinker_mqtt_wrapper(msg):
        splinker_manager.handle_mqtt_command(msg.topic, msg.payload)
    subscriber_router.subscribe_to_topic("OPEN-AIR/System/Control/Splinker/#", splinker_mqtt_wrapper)

    # --- 3. Start Phase ---
    # Start all managers that have a start() method.
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
