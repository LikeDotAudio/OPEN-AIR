"""
config_reader.py - Singleton Configuration Manager for OPEN-AIR.

Purpose:
This module defines the 'Config' class, which acts as a centralized, thread-safe 
singleton for managing application-wide settings. It handles reading from 
'config.ini', environment variable overrides, and provides a unified interface 
for accessing configuration parameters.

Primary Responsibilities:
- Provide a thread-safe singleton instance of the configuration.
- Read and parse settings from the 'config.ini' file.
- Handle automatic creation of default configuration if missing.
- Manage instance-specific identification (GUIDs, PIDs).

Assumptions and Constraints:
- Assumes a singleton pattern to ensure consistency across the application.
- Requires thread-safe initialization using locks.
- Depends on 'configparser' for INI parsing and 'pathlib' for path management.
- Expects certain environment variables (e.g., OPEN_AIR_INSTANCE_GUID) for 
  supervisor-led deployments.
"""

import configparser
import pathlib
import os
import sys
import uuid
import threading
from .config_builder import create_default_config_ini

LOCAL_DEBUG = True    # Set to False in production, True for dev on this file


class Config:
    """
    Manages application configuration settings as a thread-safe singleton.
    """

    _instance = None
    _lock = threading.Lock()  # Ensures atomic initialization in multi-threaded env.
    
    # --- Default values ---
    # These serve as fallbacks if settings are missing from config.ini.
    CURRENT_VERSION = "unknown"
    ENABLE_DEBUG_MODE = False
    ENABLE_DEBUG_SCREEN = False
    SNMP_DEBUG_ENABLE = False
    MIDI_DEBUG_ENABLE = False
    OSC_DEBUG_ENABLE = False
    AES70_DEBUG_ENABLE = False
    UI_LAYOUT_SPLIT_EQUAL = 50
    UI_LAYOUT_FULL_WEIGHT = 100
    MISSION_CRITICAL_MODE = False
    SHOW_RELOAD_BUTTON = True 
    RELOAD_CONFIG_DISPLAYED = False 
    MQTT_BROKER_ADDRESS = "localhost"
    MQTT_BROKER_PORT = 1883
    MQTT_USERNAME = None
    MQTT_PASSWORD = None
    MQTT_RETAIN_BEHAVIOR = False 
    MQTT_BASE_TOPIC = "OPEN-AIR" 

    # --- Font Settings Defaults ---
    DEFAULT_FONT_FAMILY = "Helvetica"
    DEFAULT_FONT_SIZE = 10
    HEADER_FONT_FAMILY = "Helvetica"
    HEADER_FONT_SIZE = 12

    # --- Scan Settings Defaults ---
    SCAN_GATEWAYS = True
    SCAN_USB = True
    SCAN_IP_DIRECT = True
    SCAN_AES70 = True
    SCAN_OSC = True
    SCAN_SNMP = True

    # --- OSC Settings Defaults ---
    OSC_RX_PORT = 8000
    OSC_TX_PORT = 9000
    OSC_REMOTE_IP = "127.0.0.1"

    def __init__(self):
        """
        Initializes the Config object upon its first instantiation.

        Parameters:
            None

        Returns:
            None. Internal state is updated by calling 'read_config()'.

        Side Effects and Thread-Safety:
            - Triggers filesystem I/O through 'read_config()'.
            - Sets '_initialized' flag to prevent multiple initializations.
            - This method is intended to be called only via 'get_instance()'.
        """
        # This __init__ will only be called once due to the singleton pattern
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._initialized = True
        self._LOCAL_DEBUG_state = self.ENABLE_DEBUG_SCREEN
        
        # ⚡ INSTANCE TRACKING: Unique ID for this installation
        # This identity is crucial for distinguishing messages in a multi-node 
        # MQTT network.
        self.INSTANCE_GUID = "UNKNOWN"
        
        self.read_config()  # Load configuration parameters from disk.

    @classmethod
    def get_instance(cls):
        """
        Provides access to the singleton Config instance.

        Parameters:
            None

        Returns:
            Config: The existing singleton instance, or a newly created one 
            if none exists.

        Side Effects and Thread-Safety:
            - Uses a class-level lock to ensure thread-safety during 
              initialization.
            - Guarantees that only one instance of Config exists in the process.
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
        """
        Retrieves a dictionary of global debug and logging settings.

        Parameters:
            None

        Returns:
            dict: A dictionary containing Boolean flags for various debug states.

        Side Effects and Thread-Safety:
            - Caches the generated dictionary in '_cached_global_settings' 
              to minimize overhead.
            - This property is thread-safe for reading after initial caching.
        """
        if hasattr(self, "_cached_global_settings"):
            return self._cached_global_settings

        debug_screen_enabled = self.ENABLE_DEBUG_MODE and self.ENABLE_DEBUG_SCREEN
        self._cached_global_settings = {
            "general_debug_enabled": self.ENABLE_DEBUG_MODE,
            "debug_enabled": debug_screen_enabled,
            "debug_to_file": self.ENABLE_DEBUG_MODE,
            "log_truncation_enabled": False,  # Obsolete: kept for compatibility.
            "debug_to_terminal": debug_screen_enabled,
        }
        return self._cached_global_settings

    def get_mqtt_base_topic(self):
        """
        Retrieves the configured base MQTT topic.

        Parameters:
            None

        Returns:
            str: The base topic string (e.g., 'OPEN-AIR').

        Side Effects and Thread-Safety:
            - Thread-safe for read-only access.
        """
        return self.MQTT_BASE_TOPIC

    def read_config(self):
        """
        Parses 'config.ini' and updates instance attributes accordingly.

        If 'config.ini' is missing, it creates a default version and attempts 
        to run the system setup script.

        Parameters:
            None

        Returns:
            None. Attributes of the instance are updated in-place.

        Side Effects and Thread-Safety:
            - Performs filesystem I/O (read/write).
            - May execute an external 'Setup.py' subprocess if config is missing.
            - Updates global instance state; should be called during 
              initialization.
        """
        try:
            from workers.logger.logger import initialize_logging, set_log_directory
            from loguru import logger
            from workers.initialization.path_initializer import GLOBAL_PROJECT_ROOT, initialize_paths

            # Ensure paths are initialized even if called out-of-order
            if not GLOBAL_PROJECT_ROOT:
                initialize_paths()
                from workers.initialization.path_initializer import GLOBAL_PROJECT_ROOT

            config = configparser.ConfigParser()
            config_path = GLOBAL_PROJECT_ROOT / "config.ini"

            # Recreate config if it disappeared to prevent system stall.
            if not config_path.exists():
                if LOCAL_DEBUG:
                    logger.debug(f"📜📑💻 [CONFIG] config.ini not found at "
                                 f"{config_path}. Recreating and "
                                 f"triggering setup...")
                try:
                    create_default_config_ini(config_path)
                    if LOCAL_DEBUG:
                        logger.success("✅✅✅ [SUCCESS] Default config.ini "
                                       "created.")
                except Exception as e:
                    # Gravity of Errors: Non-gated failure.
                    logger.error(f"📜📑💻 [CONFIG] ERROR: Failed to create "
                                 f"default config.ini: {e}")
                    return # Cannot proceed without config
                
                # Setup script ensures that all OS-level dependencies are 
                # satisfied after a fresh config generation.
                setup_path = GLOBAL_PROJECT_ROOT / "Installation" / "Setup.py"
                if setup_path.exists():
                    import subprocess
                    if LOCAL_DEBUG:
                        logger.info("📜📑💻 [CONFIG] Launching Setup.py...")
                    try:
                        subprocess.run([sys.executable, str(setup_path)], 
                                       check=True)
                        if LOCAL_DEBUG:
                            logger.success("✅✅✅ [SUCCESS] Setup completed "
                                           "successfully.")
                    except subprocess.CalledProcessError as e:
                        # Gravity of Errors: Non-gated failure.
                        logger.error(f"📜📑💻 [CONFIG] ERROR: Setup failed "
                                     f"with exit code {e.returncode}.")
                else:
                    if LOCAL_DEBUG:
                        logger.warning(f"⚠️⚠️⚠️ [CONFIG] WARNING: Setup script "
                                       f"not found at {setup_path}.")

            config.read(config_path)
        except Exception as e:
            print(f"CRITICAL: Failed to read or create config.ini: {e}")
            return

        if "Version" in config:
            self.CURRENT_VERSION = config["Version"].get(
                "CURRENT_VERSION", self.CURRENT_VERSION
            )

        if "Debug" in config:
            self.ENABLE_DEBUG_MODE = config["Debug"].getboolean(
                "ENABLE_DEBUG_MODE", self.ENABLE_DEBUG_MODE
            )
            self.ENABLE_DEBUG_SCREEN = config["Debug"].getboolean(
                "ENABLE_DEBUG_SCREEN", self.ENABLE_DEBUG_SCREEN
            )
            self.SNMP_DEBUG_ENABLE = config["Debug"].getboolean(
                "SNMP_DEBUG_ENABLE", self.SNMP_DEBUG_ENABLE
            )
            self.MIDI_DEBUG_ENABLE = config["Debug"].getboolean(
                "MIDI_DEBUG_ENABLE", self.MIDI_DEBUG_ENABLE
            )
            self.OSC_DEBUG_ENABLE = config["Debug"].getboolean(
                "OSC_DEBUG_ENABLE", self.OSC_DEBUG_ENABLE
            )
            self.AES70_DEBUG_ENABLE = config["Debug"].getboolean(
                "AES70_DEBUG_ENABLE", self.AES70_DEBUG_ENABLE
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
        
        if "System" in config:
            self.MISSION_CRITICAL_MODE = config["System"].getboolean(
                "MISSION_CRITICAL_MODE", self.MISSION_CRITICAL_MODE
            )
            
        # ⚡ SESSION GUID: Prioritize environment injection from Supervisor. 
        # Environment variables allow the supervisor to keep session identity 
        # across partition restarts without writing to disk.
        self.INSTANCE_GUID = os.environ.get("OPEN_AIR_INSTANCE_GUID", "UNKNOWN")
        
        # PARTITION_ID identifies if this process is CORE or UI.
        self.PARTITION_ID = os.environ.get("OPEN_AIR_PARTITION_ID", "STANDALONE")
        
        # PID ensures that logs and temporary files from different instances 
        # do not collide.
        self.PROCESS_ID = str(os.getpid())
        
        # Generate a transient GUID if not provided by a supervisor.
        if self.INSTANCE_GUID == "UNKNOWN":
            self.INSTANCE_GUID = os.urandom(8).hex().upper()
        
        # Fully qualified instance identity format: SESSION_ID:PARTITION_ID:PID
        self.FULL_INSTANCE_ID = f"{self.INSTANCE_GUID}:{self.PARTITION_ID}:{self.PROCESS_ID}"
        
        if "Fonts" in config:
            self.DEFAULT_FONT_FAMILY = config["Fonts"].get(
                "default_font_family", self.DEFAULT_FONT_FAMILY
            )
            self.DEFAULT_FONT_SIZE = int(
                config["Fonts"].get("default_font_size", self.DEFAULT_FONT_SIZE)
            )
            self.HEADER_FONT_FAMILY = config["Fonts"].get(
                "header_font_family", self.HEADER_FONT_FAMILY
            )
            self.HEADER_FONT_SIZE = int(
                config["Fonts"].get("header_font_size", self.HEADER_FONT_SIZE)
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
            self.SCAN_AES70 = config["ScanSettings"].getboolean(
                "scan_aes70", self.SCAN_AES70
            )
            self.SCAN_OSC = config["ScanSettings"].getboolean(
                "scan_osc", self.SCAN_OSC
            )
            self.SCAN_SNMP = config["ScanSettings"].getboolean(
                "scan_snmp", self.SCAN_SNMP
            )

        if "OSC" in config:
            self.OSC_RX_PORT = int(config["OSC"].get("osc_rx_port", 
                                                     self.OSC_RX_PORT))
            self.OSC_TX_PORT = int(config["OSC"].get("osc_tx_port", 
                                                     self.OSC_TX_PORT))
            self.OSC_REMOTE_IP = config["OSC"].get("osc_remote_ip", 
                                                   self.OSC_REMOTE_IP)

        if LOCAL_DEBUG:
            logger.debug("📜📑💻 [CONFIG] --- Loaded Debug Settings ---")
            logger.debug(f"📜📑💻 [CONFIG] ENABLE_DEBUG_MODE: "
                         f"{self.ENABLE_DEBUG_MODE}")
            logger.debug(f"📜📑💻 [CONFIG] ENABLE_DEBUG_SCREEN: "
                         f"{self.ENABLE_DEBUG_SCREEN}")
            logger.debug("📜📑💻 [CONFIG] -----------------------------")
