import os
import re

MAPPING = {
    "oaComProtocols.oaComAES70": "aes70",
    "oaComBroker": "broker",
    "oaComProtocols.oaComEmber": "ember",
    "oaComProtocols.oaComMidi": "midi",
    "oaComProtocols.oaComMQTT": "mqtt",
    "oaComProtocols.oaComOSC": "osc",
    "oaComProtocols.oaComREST": "rest",
    "oaComProtocols.oaComSMPTE2138": "smpte2138",
    "oaComProtocols.oaComSNMP": "snmp",
    "oaComProtocols.oaComVisa": "visa"
}

def standardize_file(file_path):
    print(f"Processing {file_path}")
    dir_name = None
    for key in MAPPING:
        if key in file_path:
            dir_name = key
            break
    
    if not dir_name:
        print(f"Skipping {file_path}, no mapping found.")
        return

    protocol = MAPPING[dir_name]
    
    with open(file_path, 'r') as f:
        content = f.read()

    # Generic replacement for ("system", "element", ...)
    # where system is one of core, ui, comms, system
    # and element is anything (we'll force it to protocol)
    # This will catch matrix_log, is_debug_allowed, assert_called_with, etc.
    
    systems = ["core", "ui", "comms", "system", "CORE", "UI", "COMMS", "SYSTEM", "CONFIG", "gui", "GUI"]
    sys_pattern = "|".join(systems)
    
    # 1. Positional: ("sys", "elem",
    # We allow any element for now and replace it with the protocol
    content = re.sub(rf'\(["\']({sys_pattern})["\']\s*,\s*["\'][^"\']+["\']\s*,', rf'("comms", "{protocol}",', content)
    
    # 2. Named: (system="sys", element="elem",
    content = re.sub(rf'system\s*=\s*["\']({sys_pattern})["\']\s*,\s*element\s*=\s*["\'][^"\']+["\']\s*,', rf'system="comms", element="{protocol}",', content)
    
    # 3. is_debug_allowed special cases (might have only 2 args)
    content = re.sub(rf'is_debug_allowed\(system\s*=\s*["\']({sys_pattern})["\']\s*,\s*element\s*=\s*["\'][^"\']+["\']\s*\)', rf'is_debug_allowed(system="comms", element="{protocol}")', content)
    content = re.sub(rf'is_debug_allowed\(["\']({sys_pattern})["\']\s*,\s*["\'][^"\']+["\']\s*\)', rf'is_debug_allowed("comms", "{protocol}")', content)

    # 4. Handle cases where it's at the end of a line or followed by a paren
    content = re.sub(rf'\(["\']({sys_pattern})["\']\s*,\s*["\'][^"\']+["\']\s*\)', rf'("comms", "{protocol}")', content)

    with open(file_path, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    import sys
    # Re-run on all previously identified files
    files = [
        "oaComBroker/Core/open_air_core.py",
        "oaComBroker/Core/protocol_router/router.py",
        "oaComBroker/Core/protocol_router/constants.py",
        "oaComBroker/Core/protocol_router/dispatch.py",
        "oaComBroker/Core/protocol_router/ingest.py",
        "oaComBroker/Core/protocol_router/settle.py",
        "oaComBroker/Managers/Failover/Manager.py",
        "oaComProtocols.oaComMidi/Interface/midi_dashboard.py",
        "oaComProtocols.oaComMidi/Core/midi_port_controller.py",
        "oaComProtocols.oaComMidi/Managers/midi_manager.py",
        "oaComProtocols.oaComMQTT/Workers/broker_monitor.py",
        "oaComProtocols.oaComMQTT/Workers/mqtt_async_worker.py",
        "oaComProtocols.oaComMQTT/Managers/mqtt_manager.py",
        "oaComProtocols.oaComMQTT/Managers/mqtt_connection.py",
        "oaComProtocols.oaComMQTT/Managers/mqtt_subscriber_router.py",
        "oaComProtocols.oaComMQTT/Tests/test_mqtt_manager.py",
        "oaComProtocols.oaComMQTT/Methods/mqtt_flattening.py",
        "oaComProtocols.oaComMQTT/Methods/delete_open_air.py",
        "oaComProtocols.oaComOSC/Workers/osc_tx_client.py",
        "oaComProtocols.oaComOSC/Workers/osc_rx_server.py",
        "oaComProtocols.oaComOSC/Managers/osc_manager.py",
        "oaComProtocols.oaComREST/Entry.py",
        "oaComProtocols.oaComREST/Workers/uvicorn_worker.py",
        "oaComProtocols.oaComREST/Managers/rest_manager.py",
        "oaComProtocols.oaComREST/Methods/port_utils.py",
        "oaComProtocols.oaComSMPTE2138/Managers/smpte2138_monitor_manager.py",
        "oaComProtocols.oaComSMPTE2138/Managers/smpte2138_bridge_manager.py",
        "oaComProtocols.oaComSNMP/Entry.py",
        "oaComProtocols.oaComSNMP/Core/snmp_state_persister.py",
        "oaComProtocols.oaComSNMP/Core/oid_map_converter.py",
        "oaComProtocols.oaComSNMP/Core/snmp_log_monitor.py",
        "oaComProtocols.oaComSNMP/Managers/snmp_manager.py",
        "oaComProtocols.oaComVisa/Workers/logic_mqtt_listen.py",
        "oaComProtocols.oaComVisa/Workers/agent_static_ip_prober.py",
        "oaComProtocols.oaComVisa/Workers/logic_disconnect_instrument.py",
        "oaComProtocols.oaComVisa/Workers/logic_connect_instrument.py",
        "oaComProtocols.oaComVisa/Workers/logic_mqtt_publisher.py",
        "oaComProtocols.oaComVisa/Workers/agent_mdns_zeroconf.py",
        "oaComProtocols.oaComVisa/Workers/visa_scanner.py",
        "oaComProtocols.oaComVisa/Workers/agent_usb_enumerator.py",
        "oaComProtocols.oaComVisa/Core/visa_proxy_fleet.py",
        "oaComProtocols.oaComVisa/Core/visa_fleet.py",
        "oaComProtocols.oaComVisa/Core/fleet_scan_mixin.py",
        "oaComProtocols.oaComVisa/Core/visa_proxy.py",
        "oaComProtocols.oaComVisa/Core/visa_safe_query.py",
        "oaComProtocols.oaComVisa/Core/visa_safe_writer.py",
        "oaComProtocols.oaComVisa/Managers/fleet_mqtt_bridge.py",
        "oaComProtocols.oaComVisa/Managers/discovery_orchestrator.py",
        "oaComProtocols.oaComVisa/FileWriters/visa_csv.py",
        "oaComProtocols.oaComVisa/FileWriters/visa_json.py",
        "oaComProtocols.oaComVisa/Methods/visa_Search.py",
        "oaComProtocols.oaComVisa/Methods/visa_list_visa_resources.py",
        "oaComProtocols.oaComVisa/Methods/visa_reset.py",
        "oaComProtocols.oaComVisa/Methods/visa_pre_flight_check.py",
        "oaComProtocols.oaComVisa/Methods/network_utils.py",
        "oaComProtocols.oaComVisa/Methods/visa_search_results.py",
        "oaComProtocols.oaComVisa/Methods/visa_reboot.py"
    ]
    for file in files:
        if os.path.exists(file):
            standardize_file(file)
        else:
            print(f"File not found: {file}")
