import os
import re

MAPPING = {
    "oaComAES70": "aes70",
    "oaComBroker": "broker",
    "oaComEmber": "ember",
    "oaComMidi": "midi",
    "oaComMQTT": "mqtt",
    "oaComOSC": "osc",
    "oaComREST": "rest",
    "oaComSMPTE2138": "smpte2138",
    "oaComSNMP": "snmp",
    "oaComVisa": "visa"
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
        "oaComMidi/Interface/midi_dashboard.py",
        "oaComMidi/Core/midi_port_controller.py",
        "oaComMidi/Managers/midi_manager.py",
        "oaComMQTT/Workers/broker_monitor.py",
        "oaComMQTT/Workers/mqtt_async_worker.py",
        "oaComMQTT/Managers/mqtt_manager.py",
        "oaComMQTT/Managers/mqtt_connection.py",
        "oaComMQTT/Managers/mqtt_subscriber_router.py",
        "oaComMQTT/Tests/test_mqtt_manager.py",
        "oaComMQTT/Methods/mqtt_flattening.py",
        "oaComMQTT/Methods/delete_open_air.py",
        "oaComOSC/Workers/osc_tx_client.py",
        "oaComOSC/Workers/osc_rx_server.py",
        "oaComOSC/Managers/osc_manager.py",
        "oaComREST/Entry.py",
        "oaComREST/Workers/uvicorn_worker.py",
        "oaComREST/Managers/rest_manager.py",
        "oaComREST/Methods/port_utils.py",
        "oaComSMPTE2138/Managers/smpte2138_monitor_manager.py",
        "oaComSMPTE2138/Managers/smpte2138_bridge_manager.py",
        "oaComSNMP/Entry.py",
        "oaComSNMP/Core/snmp_state_persister.py",
        "oaComSNMP/Core/oid_map_converter.py",
        "oaComSNMP/Core/snmp_log_monitor.py",
        "oaComSNMP/Managers/snmp_manager.py",
        "oaComVisa/Workers/logic_mqtt_listen.py",
        "oaComVisa/Workers/agent_static_ip_prober.py",
        "oaComVisa/Workers/logic_disconnect_instrument.py",
        "oaComVisa/Workers/logic_connect_instrument.py",
        "oaComVisa/Workers/logic_mqtt_publisher.py",
        "oaComVisa/Workers/agent_mdns_zeroconf.py",
        "oaComVisa/Workers/visa_scanner.py",
        "oaComVisa/Workers/agent_usb_enumerator.py",
        "oaComVisa/Core/visa_proxy_fleet.py",
        "oaComVisa/Core/visa_fleet.py",
        "oaComVisa/Core/fleet_scan_mixin.py",
        "oaComVisa/Core/visa_proxy.py",
        "oaComVisa/Core/visa_safe_query.py",
        "oaComVisa/Core/visa_safe_writer.py",
        "oaComVisa/Managers/fleet_mqtt_bridge.py",
        "oaComVisa/Managers/discovery_orchestrator.py",
        "oaComVisa/FileWriters/visa_csv.py",
        "oaComVisa/FileWriters/visa_json.py",
        "oaComVisa/Methods/visa_Search.py",
        "oaComVisa/Methods/visa_list_visa_resources.py",
        "oaComVisa/Methods/visa_reset.py",
        "oaComVisa/Methods/visa_pre_flight_check.py",
        "oaComVisa/Methods/network_utils.py",
        "oaComVisa/Methods/visa_search_results.py",
        "oaComVisa/Methods/visa_reboot.py"
    ]
    for file in files:
        if os.path.exists(file):
            standardize_file(file)
        else:
            print(f"File not found: {file}")
