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
    ENABLE_DEBUG_MODE = True
    ENABLE_DEBUG_SCREEN = True
    ENABLE_LOG_TO_FILE = True
    TIMESTAMP_LOGS = False
    
    # UI Layout
    UI_LAYOUT_SPLIT_EQUAL = 50
    UI_LAYOUT_FULL_WEIGHT = 100
    SHOW_RELOAD_BUTTON = True 
    RELOAD_CONFIG_DISPLAYED = False 
    
    # System
    MISSION_CRITICAL_MODE = False
    LANGUAGE_SELECTION = "En"
    SYSTEM_LANGUAGE = "En"
    
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
    SCAN_MIDI = True

    # VISA Settings
    VISA_PROBE_PROTOCOL = "http"
    VISA_PROBE_PATH = "html/instrumentspage.html"

    # SNMP Settings
    SNMP_PORT = 161

    # OSC Settings
    OSC_RX_PORT = 8000
    OSC_TX_PORT = 9000
    OSC_REMOTE_IP = "127.0.0.1"

    # REST Settings
    REST_HOST = "0.0.0.0"
    REST_PORT = 8000
    REST_CORS_ORIGINS = "*"

    # Debug Matrix Defaults
    DEBUG_MATRIX = {
        "MASTER_DEBUG_ENABLE": True,
        "SYS_SUP": True,
        "SYS_CORE": True,
        "SYS_UI": True,
        "SYS_GUI": True,
        "SYS_COMMS": True,
        "SYS_DATA": True,
        "SYS_ROUTER": True,
        "ELEMENT_MQTT": True,
        "ELEMENT_SNMP": True,
        "ELEMENT_OSC": True,
        "ELEMENT_REST": True,
        "ELEMENT_AES70": True,
        "ELEMENT_MIDI": True,
        "ELEMENT_GUI_BUILDER": True
    }
    MUTE_FUNCTIONS = ""
    FORCE_FUNCTIONS = ""
