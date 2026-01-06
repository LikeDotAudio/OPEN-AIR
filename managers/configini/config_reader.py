# workers/mqtt/setup/config_reader.py

import configparser
import pathlib
import threading  # Import threading for thread-safe singleton
from .config_builder import create_default_config_ini
from workers.logger.log_utils import _get_log_args  # Import _get_log_args


class Config:

    _instance = None
    _lock = (
        threading.Lock()
    )  # Class-level lock for thread-safe singleton initialization
    # --- Default values ---
    CURRENT_VERSION = "unknown"
    SKIP_DEP_CHECK = True
    CLEAN_INSTALL_MODE = False
    ENABLE_DEBUG_MODE = False
    ENABLE_DEBUG_SCREEN = False
    UI_LAYOUT_SPLIT_EQUAL = 50
    UI_LAYOUT_FULL_WEIGHT = 100
    SHOW_RELOAD_BUTTON = (
        True  # This might be redundant, but keeping for now if used elsewhere
    )
    RELOAD_CONFIG_DISPLAYED = False  # New setting
    MQTT_BROKER_ADDRESS = "localhost"
    MQTT_BROKER_PORT = 1883
    MQTT_USERNAME = None
    MQTT_PASSWORD = None
    MQTT_RETAIN_BEHAVIOR = False  # New default value
    MQTT_BASE_TOPIC = "OPEN-AIR"  # New default value

    # --- Scan Settings Defaults ---

    SCAN_GATEWAYS = True
    SCAN_USB = True
    SCAN_IP_DIRECT = True

    def __init__(self):
        # This __init__ will only be called once due to the singleton pattern
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._initialized = True
        self._local_debug_enable_state = self.ENABLE_DEBUG_SCREEN
        self.read_config()  # Read config immediately upon first instantiation

    @classmethod
    def get_instance(cls):
        """
        Returns the singleton instance of Config, ensuring it's initialized once.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = (
                        cls()
                    )  # Calls __init__ which then calls read_config()
        return cls._instance

    @property
    def global_settings(self):
        debug_screen_enabled = self.ENABLE_DEBUG_MODE and self.ENABLE_DEBUG_SCREEN
        return {
            "general_debug_enabled": self.ENABLE_DEBUG_MODE,
            "debug_enabled": debug_screen_enabled,
            "debug_to_file": self.ENABLE_DEBUG_MODE,
            "log_truncation_enabled": False,  # Obsolete
            "debug_to_terminal": debug_screen_enabled,
        }

    def get_mqtt_base_topic(self):
        """
        Returns the base MQTT topic.
        """
        return self.MQTT_BASE_TOPIC

    def read_config(self):
        """
        Reads configuration from config.ini and updates instance attributes.
        If config.ini is not found, a default one is created.
        """
        from workers.logger.logger import debug_logger  # Import debug_logger

        config = configparser.ConfigParser()
        project_root = pathlib.Path(__file__).resolve().parent.parent.parent
        config_path = project_root / "config.ini"

        # If config.ini does not exist, create a default one
        if not config_path.exists():
            debug_logger(
                message=f"📄 config.ini not found at {config_path}. Creating default config.ini...",
                **_get_log_args(),
            )
            create_default_config_ini(config_path)
            debug_logger(message="✅ Default config.ini created.", **_get_log_args())

        # Now read the (possibly newly created) config.ini
        config.read(config_path)

        if "Version" in config:
            self.CURRENT_VERSION = config["Version"].get(
                "CURRENT_VERSION", self.CURRENT_VERSION
            )

        if "Mode" in config:
            self.SKIP_DEP_CHECK = config["Mode"].getboolean(
                "SKIP_DEP_CHECK", self.SKIP_DEP_CHECK
            )
            self.CLEAN_INSTALL_MODE = config["Mode"].getboolean(
                "CLEAN_INSTALL_MODE", self.CLEAN_INSTALL_MODE
            )

        if "Debug" in config:
            self.ENABLE_DEBUG_MODE = config["Debug"].getboolean(
                "ENABLE_DEBUG_MODE", self.ENABLE_DEBUG_MODE
            )
            self.ENABLE_DEBUG_SCREEN = config["Debug"].getboolean(
                "ENABLE_DEBUG_SCREEN", self.ENABLE_DEBUG_SCREEN
            )

            if "UI" in config:

                self.UI_LAYOUT_SPLIT_EQUAL = int(
                    config["UI"].get("LAYOUT_SPLIT_EQUAL", self.UI_LAYOUT_SPLIT_EQUAL)
                )
                self.UI_LAYOUT_FULL_WEIGHT = int(
                    config["UI"].get("LAYOUT_FULL_WEIGHT", self.UI_LAYOUT_FULL_WEIGHT)
                )
                self.SHOW_RELOAD_BUTTON = config["UI"].getboolean(
                    "SHOW_RELOAD_BUTTON", self.SHOW_RELOAD_BUTTON
                )
                self.RELOAD_CONFIG_DISPLAYED = config["UI"].getboolean(
                    "RELOAD_CONFIG_DISPLAYED", self.RELOAD_CONFIG_DISPLAYED
                )

        if "MQTT" in config:
            self.MQTT_BROKER_ADDRESS = config["MQTT"].get(
                "BROKER_ADDRESS", self.MQTT_BROKER_ADDRESS
            )
            self.MQTT_BROKER_PORT = int(
                config["MQTT"].get("BROKER_PORT", self.MQTT_BROKER_PORT)
            )
            self.MQTT_USERNAME = config["MQTT"].get("MQTT_USERNAME", self.MQTT_USERNAME)
            self.MQTT_PASSWORD = config["MQTT"].get("MQTT_PASSWORD", self.MQTT_PASSWORD)
            self.MQTT_RETAIN_BEHAVIOR = config["MQTT"].getboolean(
                "MQTT_RETAIN_BEHAVIOR", self.MQTT_RETAIN_BEHAVIOR
            )
            self.MQTT_BASE_TOPIC = config["MQTT"].get(
                "MQTT_BASE_TOPIC", self.MQTT_BASE_TOPIC
            )

        if "Protocols" in config:
            pass

        if "ScanSettings" in config:
            self.SCAN_GATEWAYS = config["ScanSettings"].getboolean(
                "scan_gateways", self.SCAN_GATEWAYS
            )
            self.SCAN_USB = config["ScanSettings"].getboolean("scan_usb", self.SCAN_USB)
            self.SCAN_IP_DIRECT = config["ScanSettings"].getboolean(
                "scan_ip_direct", self.SCAN_IP_DIRECT
            )

        debug_logger(message="--- Loaded Debug Settings ---", **_get_log_args())
        debug_logger(
            message=f"ENABLE_DEBUG_MODE: {self.ENABLE_DEBUG_MODE}", **_get_log_args()
        )
        debug_logger(
            message=f"ENABLE_DEBUG_SCREEN: {self.ENABLE_DEBUG_SCREEN}",
            **_get_log_args(),
        )
        debug_logger(message="-----------------------------", **_get_log_args())
