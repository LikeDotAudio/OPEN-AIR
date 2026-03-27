# Core/composition_root.py
# Author: Anthony Peter Kuzub
# Version: 20260322.Modular.1
#
# Description: Composition Root for the UI Partition.

import tkinter as tk
from loguru import logger

# --- Framework Imports ---
from oaComMQTT.Managers.mqtt_connection import MqttConnectionManager
from oaComMQTT.Managers.mqtt_subscriber_router import MqttSubscriberRouter
from oaStateCache.Core.state_cache import StateRegistry
from oaTranslator.Core.state_mirror_engine import StateMirrorEngine
from oaComBroker.Core.protocol_router import ProtocolRouter

# --- External Managers ---
from oaComOSC.Managers.osc_manager import OSCManager
from oaComSNMP.Managers.snmp_manager import SNMPManager
from oaComMidi.Managers.midi_manager import MidiManager
from oaSplinker.Core.splinker import ControlBroker

class UICompositionRoot:
    """
    Orchestrates the creation and dependency injection of all UI-level services.
    Acts as the 'brain' for service orchestration within the UI partition.
    """

    def __init__(self, root, app_constants):
        self.root = root
        self.app_constants = app_constants
        self.services = {
            "app": None,
            "mqtt_conn": None,
            "sub_router": None,
            "state_cache": None,
            "mirror_engine": None,
            "osc_manager": None,
            "snmp_manager": None,
            "midi_manager": None,
            "splinker_manager": None,
            "protocol_router": None
        }

    def build_services(self):
        """
        Instantiates concrete service implementations and maps their dependencies.
        """
        logger.debug("🏗️ [ROOT] Composing UI Services...")

        # 1. Base Communication Layer
        mqtt_conn = MqttConnectionManager()
        sub_router = MqttSubscriberRouter()
        
        # 2. State & Mirroring Layer
        state_cache = StateRegistry(mqtt_conn)
        state_cache.subscriber_router = sub_router
        
        mirror_engine = StateMirrorEngine(
            base_topic="OPEN-AIR", 
            subscriber_router=sub_router, 
            root=self.root, 
            state_cache_manager=state_cache
        )
        state_cache.state_mirror_engine = mirror_engine

        # 3. Protocol Routing & Specialized Managers
        protocol_router = ProtocolRouter.get_instance()
        protocol_router.set_mqtt_manager(mqtt_conn)
        
        splinker = ControlBroker.get_instance(state_cache, mqtt_conn)
        protocol_router.set_splinker_manager(splinker)

        # 4. Map to registry
        self.services.update({
            "mqtt_conn": mqtt_conn,
            "sub_router": sub_router,
            "state_cache": state_cache,
            "mirror_engine": mirror_engine,
            "protocol_router": protocol_router,
            "splinker_manager": splinker
        })

        # 5. Optional Managers (Conditional based on config)
        if self.app_constants.SCAN_OSC:
            self.services["osc_manager"] = OSCManager(state_cache, mqtt_conn, run_bridge=False)
        
        if self.app_constants.SCAN_SNMP:
            import oaComSNMP.Entry as snmp_entry
            self.services["snmp_manager"] = snmp_entry.get_manager(
                state_cache_manager=state_cache, 
                mqtt_connection_manager=mqtt_conn, 
                subscriber_router=sub_router, 
                run_bridge=False
            )
            
        self.services["midi_manager"] = MidiManager(state_cache, run_bridge=False)

        logger.success("✅ [ROOT] UI Service Graph Composed.")
        return self.services

    def get_bootstrap_dependencies(self):
        """
        Returns a dictionary of services suitable for the BootstrapEngine.
        """
        return self.services
