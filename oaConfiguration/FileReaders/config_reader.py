# FileReaders/config_reader.py
# Author: Anthony Peter Kuzub
# Version: 20260316.1
#
# Description: Modularized Configuration Manager.

import threading
from loguru import logger

# --- EXTRACTED CORE MODULES ---
from ..Core.config_defaults import ConfigDefaults
from ..Core.identity import IdentityManager
from ..Core.config_loader import ConfigLoader

LOCAL_DEBUG = False

class Config(ConfigDefaults):
    """
    Manages application configuration settings as a thread-safe singleton.
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

    def _s_get(self, config, sec, key, fallback, parser=None):
        """Helper to get and parse config values with fallbacks."""
        if sec not in config: return fallback
        if parser == "bool": return config[sec].getboolean(key, fallback)
        if parser == "int": return int(config[sec].get(key, fallback))
        return config[sec].get(key, fallback)

    def _parse_debug_settings(self, config):
        self.ENABLE_DEBUG_MODE = self._s_get(config, "Debug", "ENABLE_DEBUG_MODE", self.ENABLE_DEBUG_MODE, "bool")
        self.ENABLE_DEBUG_SCREEN = self._s_get(config, "Debug", "ENABLE_DEBUG_SCREEN", self.ENABLE_DEBUG_SCREEN, "bool")
        self.SNMP_DEBUG_ENABLE = self._s_get(config, "Debug", "SNMP_DEBUG_ENABLE", self.SNMP_DEBUG_ENABLE, "bool")
        self.MIDI_DEBUG_ENABLE = self._s_get(config, "Debug", "MIDI_DEBUG_ENABLE", self.MIDI_DEBUG_ENABLE, "bool")
        self.OSC_DEBUG_ENABLE = self._s_get(config, "Debug", "OSC_DEBUG_ENABLE", self.OSC_DEBUG_ENABLE, "bool")
        self.AES70_DEBUG_ENABLE = self._s_get(config, "Debug", "AES70_DEBUG_ENABLE", self.AES70_DEBUG_ENABLE, "bool")

    def _parse_ui_settings(self, config):
        self.UI_LAYOUT_SPLIT_EQUAL = self._s_get(config, "UI", "LAYOUT_SPLIT_EQUAL", self.UI_LAYOUT_SPLIT_EQUAL, "int")
        self.UI_LAYOUT_FULL_WEIGHT = self._s_get(config, "UI", "LAYOUT_FULL_WEIGHT", self.UI_LAYOUT_FULL_WEIGHT, "int")
        self.SHOW_RELOAD_BUTTON = self._s_get(config, "UI", "SHOW_RELOAD_BUTTON", self.SHOW_RELOAD_BUTTON, "bool")
        self.RELOAD_CONFIG_DISPLAYED = self._s_get(config, "UI", "RELOAD_CONFIG_DISPLAYED", self.RELOAD_CONFIG_DISPLAYED, "bool")

    def _parse_font_settings(self, config):
        self.DEFAULT_FONT_FAMILY = self._s_get(config, "Fonts", "default_font_family", self.DEFAULT_FONT_FAMILY)
        self.DEFAULT_FONT_SIZE = self._s_get(config, "Fonts", "default_font_size", self.DEFAULT_FONT_SIZE, "int")
        self.HEADER_FONT_FAMILY = self._s_get(config, "Fonts", "header_font_family", self.HEADER_FONT_FAMILY)
        self.HEADER_FONT_SIZE = self._s_get(config, "Fonts", "header_font_size", self.HEADER_FONT_SIZE, "int")

    def _parse_mqtt_settings(self, config):
        self.MQTT_BROKER_ADDRESS = self._s_get(config, "MQTT", "BROKER_ADDRESS", self.MQTT_BROKER_ADDRESS)
        self.MQTT_BROKER_PORT = self._s_get(config, "MQTT", "BROKER_PORT", self.MQTT_BROKER_PORT, "int")
        self.MQTT_USERNAME = self._s_get(config, "MQTT", "MQTT_USERNAME", self.MQTT_USERNAME)
        self.MQTT_PASSWORD = self._s_get(config, "MQTT", "MQTT_PASSWORD", self.MQTT_PASSWORD)
        self.MQTT_RETAIN_BEHAVIOR = self._s_get(config, "MQTT", "MQTT_RETAIN_BEHAVIOR", self.MQTT_RETAIN_BEHAVIOR, "bool")
        self.MQTT_BASE_TOPIC = self._s_get(config, "MQTT", "MQTT_BASE_TOPIC", self.MQTT_BASE_TOPIC)

    def _parse_scan_settings(self, config):
        self.SCAN_GATEWAYS = self._s_get(config, "ScanSettings", "scan_gateways", self.SCAN_GATEWAYS, "bool")
        self.SCAN_USB = self._s_get(config, "ScanSettings", "scan_usb", self.SCAN_USB, "bool")
        self.SCAN_IP_DIRECT = self._s_get(config, "ScanSettings", "scan_ip_direct", self.SCAN_IP_DIRECT, "bool")
        self.SCAN_AES70 = self._s_get(config, "ScanSettings", "scan_aes70", self.SCAN_AES70, "bool")
        self.SCAN_OSC = self._s_get(config, "ScanSettings", "scan_osc", self.SCAN_OSC, "bool")
        self.SCAN_SNMP = self._s_get(config, "ScanSettings", "scan_snmp", self.SCAN_SNMP, "bool")

    def _parse_visa_settings(self, config):
        self.VISA_PROBE_PROTOCOL = self._s_get(config, "VISA", "probe_protocol", self.VISA_PROBE_PROTOCOL)
        self.VISA_PROBE_PATH = self._s_get(config, "VISA", "probe_path", self.VISA_PROBE_PATH)

    def _parse_snmp_settings(self, config):
        self.SNMP_PORT = self._s_get(config, "SNMP", "snmp_port", self.SNMP_PORT, "int")

    def _parse_osc_settings(self, config):
        self.OSC_RX_PORT = self._s_get(config, "OSC", "osc_rx_port", self.OSC_RX_PORT, "int")
        self.OSC_TX_PORT = self._s_get(config, "OSC", "osc_tx_port", self.OSC_TX_PORT, "int")
        self.OSC_REMOTE_IP = self._s_get(config, "OSC", "osc_remote_ip", self.OSC_REMOTE_IP)

    def read_config(self):
        from oaOchestration.Core.path_initializer import GLOBAL_PROJECT_ROOT, initialize_paths
        if not GLOBAL_PROJECT_ROOT: initialize_paths()
        
        from oaOchestration.Core.path_initializer import GLOBAL_PROJECT_ROOT
        config_path = GLOBAL_PROJECT_ROOT / "config.ini"
        setup_path = GLOBAL_PROJECT_ROOT / "oaInstallation" / "Setup.py"
        
        config = ConfigLoader.load(config_path, setup_path, LOCAL_DEBUG)
        if not config: return

        self.CURRENT_VERSION = self._s_get(config, "Version", "CURRENT_VERSION", self.CURRENT_VERSION)
        self.MISSION_CRITICAL_MODE = self._s_get(config, "System", "MISSION_CRITICAL_MODE", self.MISSION_CRITICAL_MODE, "bool")

        self._parse_debug_settings(config)
        self._parse_ui_settings(config)
        self._parse_font_settings(config)
        self._parse_mqtt_settings(config)
        self._parse_scan_settings(config)
        self._parse_visa_settings(config)
        self._parse_snmp_settings(config)
        self._parse_osc_settings(config)

        if LOCAL_DEBUG:
            logger.debug(f"📜 [CONFIG] Loaded: Version {self.CURRENT_VERSION}, Debug: {self.ENABLE_DEBUG_MODE}")

    def get_mqtt_base_topic(self):
        """Returns the MQTT root topic for the application."""
        return self.MQTT_BASE_TOPIC
