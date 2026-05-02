# oaGui/Managers/bootstrap/protocol_service_igniter.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Service for starting protocol routers and optional managers (OSC, SNMP, etc.).

def ignite_protocol_services(splash, services):
    """Starts the main protocol router and any configured optional protocol managers."""
    splash.set_status(message="Starting Protocol Services...")
    
    if "protocol_router" in services:
        services["protocol_router"].start()

    optional_map = {
        "osc_manager": "OSC",
        "snmp_manager": "SNMP",
        "midi_manager": "MIDI",
        "rest_manager": "REST API"
    }

    for key, display_name in optional_map.items():
        service = services.get(key)
        if service:
            splash.set_status(message=f"Starting {display_name}...")
            service.start()
