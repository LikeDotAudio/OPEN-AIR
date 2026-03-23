# Core/config_defaults.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

class ConfigDefaults:
    """Standardized default values for the OPEN-AIR configuration schema."""
    
    # Versioning
    CURRENT_VERSION = "unknown"
    
    # Debugging
    ENABLE_DEBUG_MODE = False
    ENABLE_DEBUG_SCREEN = False
    SNMP_DEBUG_ENABLE = False
    MIDI_DEBUG_ENABLE = False
    OSC_DEBUG_ENABLE = False
    AES70_DEBUG_ENABLE = False
    
    # UI Layout
    UI_LAYOUT_SPLIT_EQUAL = 50
    UI_LAYOUT_FULL_WEIGHT = 100
    SHOW_RELOAD_BUTTON = True 
    RELOAD_CONFIG_DISPLAYED = False 
    
    # System
    MISSION_CRITICAL_MODE = False
    
    # MQTT
    MQTT_BROKER_ADDRESS = "localhost"
    MQTT_BROKER_PORT = 1883
    MQTT_USERNAME = None
    MQTT_PASSWORD = None
    MQTT_RETAIN_BEHAVIOR = False 
    MQTT_BASE_TOPIC = "OPEN-AIR" 

    # Font Settings
    DEFAULT_FONT_FAMILY = "Helvetica"
    DEFAULT_FONT_SIZE = 10
    HEADER_FONT_FAMILY = "Helvetica"
    HEADER_FONT_SIZE = 12

    # Scan Settings
    SCAN_GATEWAYS = True
    SCAN_USB = True
    SCAN_IP_DIRECT = True
    SCAN_AES70 = True
    SCAN_OSC = True
    SCAN_SNMP = True

    # VISA Settings
    VISA_PROBE_PROTOCOL = "http"
    VISA_PROBE_PATH = "html/instrumentspage.html"

    # SNMP Settings
    SNMP_PORT = 161

    # OSC Settings
    OSC_RX_PORT = 8000
    OSC_TX_PORT = 9000
    OSC_REMOTE_IP = "127.0.0.1"
