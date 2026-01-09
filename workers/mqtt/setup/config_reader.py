# setup/config_reader.py
#
# This module defines the Config singleton class, responsible for reading and managing application configuration settings from `config.ini`.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20250821.200641.1

import configparser
import pathlib
import threading  # Import threading for thread-safe singleton


class Config:
    _instance = None
    _lock = (
        threading.Lock()
    )  # Class-level lock for thread-safe singleton initialization

    # --- Default values ---
    CURRENT_VERSION = "unknown"
    PERFORMANCE_MODE = True
    SKIP_DEP_CHECK = True
    CLEAN_INSTALL_MODE = False
    ENABLE_DEBUG_MODE = False
    ENABLE_DEBUG_FILE = False
    ENABLE_DEBUG_SCREEN = False
    LOG_TRUNCATION_ENABLED = False
    UI_LAYOUT_SPLIT_EQUAL = 50
    UI_LAYOUT_FULL_WEIGHT = 100
    MQTT_BROKER_ADDRESS = "localhost"
    MQTT_BROKER_PORT = 1883
    MQTT_USERNAME = None
    MQTT_PASSWORD = None

    # Implements the singleton pattern, ensuring only one instance of Config exists.
    # This method ensures that the `Config` class is instantiated only once across
    # the entire application, providing a single source of truth for configuration.
    # Inputs:
    #     cls: The class itself.
    #     *args: Positional arguments for the constructor.
    #     **kwargs: Keyword arguments for the constructor.
    # Outputs:
    #     Config: The singleton instance of the Config class.
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = (
                        cls()
                    )  # Calls __init__ which then calls read_config()
        return cls._instance

    # Initializes the Config instance by reading settings from `config.ini`.
    # This constructor sets up default values for all configuration parameters
    # and then immediately attempts to override them by reading from the
    # `config.ini` file, if present.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def __init__(self):
        # This __init__ will only be called once due to the singleton pattern
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._initialized = True
        self._local_debug_enable_state = self.ENABLE_DEBUG_SCREEN
        self.read_config()  # Read config immediately upon first instantiation

    # Returns the singleton instance of the Config class.
    # This class method provides the standard way to access the application's
    # configuration settings, ensuring that the `Config` object is properly
    # initialized and unique.
    # Inputs:
    #     cls: The class itself.
    # Outputs:
    #     Config: The singleton instance of the Config class.
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

    # Provides access to a dictionary of global debug settings.
    # This property aggregates key debug-related settings, making them easily
    # accessible as a single dictionary.
    # Inputs:
    #     self: The instance of the class.
    # Outputs:
    #     dict: A dictionary containing global debug settings.
    @property
    def global_settings(self):
        return {
            "general_debug_enabled": self.ENABLE_DEBUG_MODE,
            "debug_enabled": self.ENABLE_DEBUG_SCREEN,
            "debug_to_file": self.ENABLE_DEBUG_FILE,
            "log_truncation_enabled": self.LOG_TRUNCATION_ENABLED,
        }

    # Reads configuration settings from the `config.ini` file.
    # This method parses the `config.ini` file located in the project root
    # and updates the instance attributes with the values found in the file.
    # If the file is not found, default settings are used.
    # Inputs:
    #     self: The instance of the class.
    # Outputs:
    #     None.
    def read_config(self):
        """
        Reads configuration from config.ini and updates instance attributes.
        """
        config = configparser.ConfigParser()
        project_root = pathlib.Path(__file__).parent.parent.parent.parent
        config_path = project_root / "config.ini"

        if config_path.exists():
            config.read(config_path)

            if "Version" in config:
                self.CURRENT_VERSION = config["Version"].get(
                    "CURRENT_VERSION", self.CURRENT_VERSION
                )

            if "Mode" in config:
                self.PERFORMANCE_MODE = config["Mode"].getboolean(
                    "PERFORMANCE_MODE", self.PERFORMANCE_MODE
                )
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
                self.ENABLE_DEBUG_FILE = config["Debug"].getboolean(
                    "ENABLE_DEBUG_FILE", self.ENABLE_DEBUG_FILE
                )
                self.ENABLE_DEBUG_SCREEN = config["Debug"].getboolean(
                    "ENABLE_DEBUG_SCREEN", self.ENABLE_DEBUG_SCREEN
                )
                self.LOG_TRUNCATION_ENABLED = config["Debug"].getboolean(
                    "LOG_TRUNCATION_ENABLED", self.LOG_TRUNCATION_ENABLED
                )

            if "UI" in config:
                self.UI_LAYOUT_SPLIT_EQUAL = int(
                    config["UI"].get("LAYOUT_SPLIT_EQUAL", self.UI_LAYOUT_SPLIT_EQUAL)
                )
                self.UI_LAYOUT_FULL_WEIGHT = int(
                    config["UI"].get("LAYOUT_FULL_WEIGHT", self.UI_LAYOUT_FULL_WEIGHT)
                )

            if "MQTT" in config:
                self.MQTT_BROKER_ADDRESS = config["MQTT"].get(
                    "BROKER_ADDRESS", self.MQTT_BROKER_ADDRESS
                )
                self.MQTT_BROKER_PORT = int(
                    config["MQTT"].get("BROKER_PORT", self.MQTT_BROKER_PORT)
                )
                self.MQTT_USERNAME = config["MQTT"].get(
                    "MQTT_USERNAME", self.MQTT_USERNAME
                )
                self.MQTT_PASSWORD = config["MQTT"].get(
                    "MQTT_PASSWORD", self.MQTT_PASSWORD
                )

            print("--- Loaded Debug Settings ---")
            print(f"ENABLE_DEBUG_MODE: {self.ENABLE_DEBUG_MODE}")
            print(f"ENABLE_DEBUG_FILE: {self.ENABLE_DEBUG_FILE}")
            print(f"ENABLE_DEBUG_SCREEN: {self.ENABLE_DEBUG_SCREEN}")
            print("-----------------------------")
        else:
            print(
                f"Warning: config.ini not found at {config_path}. Using default settings."
            )