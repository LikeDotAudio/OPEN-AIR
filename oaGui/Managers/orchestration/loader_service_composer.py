# Managers/loader_service_composer.py
# Author: Anthony Peter Kuzub
# Version: 20260322.Modular.1
#
# Description: Composition Root for the UI Partition.

import inspect

from oaComBroker.Core.protocol_router.manager import ProtocolRouter

# --- Standard Debug Logging Setup ---
# --- Framework Imports ---
from oaComProtocols.oaComMQTT.Managers.mqtt_connection import MqttConnectionManager
from oaComProtocols.oaComMQTT.Managers.mqtt_subscriber_router import MqttSubscriberRouter

# --- External Managers ---
from oaComProtocols.oaComOSC.Managers.osc_manager import OSCManager
from oaComProtocols.oaComREST.Managers.rest_manager import RESTManager
from oaLogging.Methods.matrix_gate import matrix_log
from oaSplinker.Core.splinker import ControlBroker
from oaStateCache.Core.state_cache import StateRegistry
from oaStateCache.Core.state_mirror_engine import StateMirrorEngine


class LoaderServiceComposer:
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
        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, "🏗️ [ROOT] Composing UI Services...", level="DEBUG")

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

        # Optional Managers (Conditional based on config)
        if self.app_constants.SCAN_OSC:
            self.services["osc_manager"] = OSCManager(state_cache_manager=state_cache, mqtt_connection_manager=mqtt_conn, run_bridge=True)
            if hasattr(self.services["osc_manager"], "start"): self.services["osc_manager"].start()

        if self.app_constants.SCAN_SNMP:
            import oaComProtocols.oaComSNMP.Entry as snmp_entry
            snmp_mgr = snmp_entry.get_manager(state_cache_manager=state_cache, mqtt_connection_manager=mqtt_conn, subscriber_router=sub_router, run_bridge=False)
            self.services["snmp_manager"] = snmp_mgr
            snmp_mgr.start()
            protocol_router.set_snmp_manager(snmp_mgr)

        if self.app_constants.SCAN_MIDI:
            import oaComProtocols.oaComMidi.Entry as midi_entry
            self.services["midi_manager"] = midi_entry.get_manager(state_cache_manager=state_cache, run_bridge=False)

        # self.services["midi_manager"] = MidiManager(state_cache, run_bridge=False)
        self.services["rest_manager"] = RESTManager(state_cache, protocol_router)

        # ST 2138 SMPTE2138 Monitor Logic
        import oaComProtocols.oaComSMPTE2138.Entry as smpte2138_monitor_entry
        self.services["smpte2138_monitor_manager"] = smpte2138_monitor_entry.start_monitor(mqtt_conn, sub_router)

        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, "✅ [ROOT] UI Service Graph Composed.", level="SUCCESS")
        return self.services

    def get_bootstrap_dependencies(self):
        """
        Returns a dictionary of services suitable for the BootstrapEngine.
        """
        return self.services
