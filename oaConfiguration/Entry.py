# oaConfiguration/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260330.1000.1 # Updated version for structure change
#
# Description: Configuration Module Entry Point.

"""
oaConfiguration/Entry.py - The sole orchestrator for the Configuration Module.

Purpose:
This file is the public entry point for 'oaConfiguration'. It manages the
lifecycle of the configuration manager and exports the core 'Config'
singleton and its associated functions to the rest of the project.
"""

from .FileReaders.config_reader import Config
from .Methods.config_validator import validate_configuration
# from .Methods.console_encoder import ConsoleEncoder

class ConfigurationEntry:
    """Entry point for configuration management services."""
    def __init__(self):
        print("📡📥📥 [INBOUND] Initializing ConfigurationEntry...")
        self.config_instance = Config()
        pass

    def start(self):
        """Starts the configuration service (e.g., loads default config if needed)."""
        print("⚙️ [CONFIG] Starting Configuration service...")
        # Placeholder for start logic, potentially loading a default config
        # or ensuring configuration is ready.
        self.config_instance.initialize() # Example: Ensure config is loaded
        pass

    def stop(self):
        """Stops the configuration service."""
        print("🛑 [CONFIG] Stopping Configuration service...")
        # Placeholder for stop logic, e.g., saving pending changes if applicable
        pass

    def status(self):
        """Returns the current status of the configuration service."""
        print("ℹ️ [CONFIG] Checking Configuration service status...")
        # Placeholder for status check logic
        return "initialized" # Example status

def get_config_instance():
    """Returns the singleton Config instance."""
    # Ensure config is initialized before returning
    if not Config._instance: # Assuming Config is a singleton with _instance attribute
        Config().initialize()
    return Config()

def initialize_config(config_path="config.ini", silent=True):
    """
    Initializes the configuration from the specified path.
    """
    # Note: This function might need to interact with ConfigurationEntry if 
    # it's meant to be the primary initialization mechanism. For now, it
    # directly calls the Config class method.
    return Config().initialize(config_path, silent)

def validate(output_func=None):
    """
    Validates the current configuration.
    """
    return validate_configuration(output_func)

def get_encoder():
    """Returns the ConsoleEncoder for output formatting."""
    return None

# Standardized exports
__all__ = [
    "ConfigurationEntry",
    "Config",
    "get_config_instance",
    "initialize_config",
    "validate",
    "get_encoder"
]
