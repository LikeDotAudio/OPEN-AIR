# configini/config_reader.py
# Modularized Configuration Manager.
# Version 20260315.Modular.1

import threading
from loguru import logger

# --- EXTRACTED CORE MODULES ---
from .core.config_defaults import ConfigDefaults
from .core.identity_manager import IdentityManager
from .core.config_loader import ConfigLoader

LOCAL_DEBUG = True

class Config(ConfigDefaults):
    """
    Manages application configuration settings as a thread-safe singleton.
    Refactored into modular components for loading, identity, and defaults.
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized: return
        self._initialized = True
        
        # 1. Initialize Identity
        ids = IdentityManager.initialize()
        for k, v in ids.items(): setattr(self, k, v)
        
        # 2. Read Configuration
        self.read_config()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None: cls._instance = cls()
        return cls._instance

    @property
    def global_settings(self):
        if hasattr(self, "_cached_global_settings"): return self._cached_global_settings
        ds_enabled = self.ENABLE_DEBUG_MODE and self.ENABLE_DEBUG_SCREEN
        self._cached_global_settings = {
            "general_debug_enabled": self.ENABLE_DEBUG_MODE,
            "debug_enabled": ds_enabled,
            "debug_to_file": self.ENABLE_DEBUG_MODE,
            "debug_to_terminal": ds_enabled,
        }
        return self._cached_global_settings

    def read_config(self):
        from workers.initialization.path_initializer import GLOBAL_PROJECT_ROOT, initialize_paths
        if not GLOBAL_PROJECT_ROOT: initialize_paths()
        
        from workers.initialization.path_initializer import GLOBAL_PROJECT_ROOT
        cp = GLOBAL_PROJECT_ROOT / "config.ini"
        sp = GLOBAL_PROJECT_ROOT / "Installation" / "Setup.py"
        
        config = ConfigLoader.load(cp, sp, LOCAL_DEBUG)
        if not config: return

        # --- Section Mapping ---
        def s_get(sec, key, fallback, parser=None):
            if sec not in config: return fallback
            if parser == "bool": return config[sec].getboolean(key, fallback)
            if parser == "int": return int(config[sec].get(key, fallback))
            return config[sec].get(key, fallback)

        self.CURRENT_VERSION = s_get("Version", "CURRENT_VERSION", self.CURRENT_VERSION)
        
        self.ENABLE_DEBUG_MODE = s_get("Debug", "ENABLE_DEBUG_MODE", self.ENABLE_DEBUG_MODE, "bool")
        self.ENABLE_DEBUG_SCREEN = s_get("Debug", "ENABLE_DEBUG_SCREEN", self.ENABLE_DEBUG_SCREEN, "bool")
        self.SNMP_DEBUG_ENABLE = s_get("Debug", "SNMP_DEBUG_ENABLE", self.SNMP_DEBUG_ENABLE, "bool")
        self.MIDI_DEBUG_ENABLE = s_get("Debug", "MIDI_DEBUG_ENABLE", self.MIDI_DEBUG_ENABLE, "bool")
        self.OSC_DEBUG_ENABLE = s_get("Debug", "OSC_DEBUG_ENABLE", self.OSC_DEBUG_ENABLE, "bool")
        self.AES70_DEBUG_ENABLE = s_get("Debug", "AES70_DEBUG_ENABLE", self.AES70_DEBUG_ENABLE, "bool")

        self.UI_LAYOUT_SPLIT_EQUAL = s_get("UI", "LAYOUT_SPLIT_EQUAL", self.UI_LAYOUT_SPLIT_EQUAL, "int")
        self.UI_LAYOUT_FULL_WEIGHT = s_get("UI", "LAYOUT_FULL_WEIGHT", self.UI_LAYOUT_FULL_WEIGHT, "int")
        self.SHOW_RELOAD_BUTTON = s_get("UI", "SHOW_RELOAD_BUTTON", self.SHOW_RELOAD_BUTTON, "bool")
        self.RELOAD_CONFIG_DISPLAYED = s_get("UI", "RELOAD_CONFIG_DISPLAYED", self.RELOAD_CONFIG_DISPLAYED, "bool")
        
        self.MISSION_CRITICAL_MODE = s_get("System", "MISSION_CRITICAL_MODE", self.MISSION_CRITICAL_MODE, "bool")
        
        self.DEFAULT_FONT_FAMILY = s_get("Fonts", "default_font_family", self.DEFAULT_FONT_FAMILY)
        self.DEFAULT_FONT_SIZE = s_get("Fonts", "default_font_size", self.DEFAULT_FONT_SIZE, "int")
        self.HEADER_FONT_FAMILY = s_get("Fonts", "header_font_family", self.HEADER_FONT_FAMILY)
        self.HEADER_FONT_SIZE = s_get("Fonts", "header_font_size", self.HEADER_FONT_SIZE, "int")

        self.MQTT_BROKER_ADDRESS = s_get("MQTT", "BROKER_ADDRESS", self.MQTT_BROKER_ADDRESS)
        self.MQTT_BROKER_PORT = s_get("MQTT", "BROKER_PORT", self.MQTT_BROKER_PORT, "int")
        self.MQTT_USERNAME = s_get("MQTT", "MQTT_USERNAME", self.MQTT_USERNAME)
        self.MQTT_PASSWORD = s_get("MQTT", "MQTT_PASSWORD", self.MQTT_PASSWORD)
        self.MQTT_RETAIN_BEHAVIOR = s_get("MQTT", "MQTT_RETAIN_BEHAVIOR", self.MQTT_RETAIN_BEHAVIOR, "bool")
        self.MQTT_BASE_TOPIC = s_get("MQTT", "MQTT_BASE_TOPIC", self.MQTT_BASE_TOPIC)

        self.SCAN_GATEWAYS = s_get("ScanSettings", "scan_gateways", self.SCAN_GATEWAYS, "bool")
        self.SCAN_USB = s_get("ScanSettings", "scan_usb", self.SCAN_USB, "bool")
        self.SCAN_IP_DIRECT = s_get("ScanSettings", "scan_ip_direct", self.SCAN_IP_DIRECT, "bool")
        self.SCAN_AES70 = s_get("ScanSettings", "scan_aes70", self.SCAN_AES70, "bool")
        self.SCAN_OSC = s_get("ScanSettings", "scan_osc", self.SCAN_OSC, "bool")
        self.SCAN_SNMP = s_get("ScanSettings", "scan_snmp", self.SCAN_SNMP, "bool")

        self.OSC_RX_PORT = s_get("OSC", "osc_rx_port", self.OSC_RX_PORT, "int")
        self.OSC_TX_PORT = s_get("OSC", "osc_tx_port", self.OSC_TX_PORT, "int")
        self.OSC_REMOTE_IP = s_get("OSC", "osc_remote_ip", self.OSC_REMOTE_IP)

        if LOCAL_DEBUG:
            logger.debug(f"📜 [CONFIG] Loaded: Version {self.CURRENT_VERSION}, Debug: {self.ENABLE_DEBUG_MODE}")

    def get_mqtt_base_topic(self):
        """Returns the MQTT root topic for the application."""
        return self.MQTT_BASE_TOPIC
