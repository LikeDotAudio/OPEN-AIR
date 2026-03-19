"""
oaConfiguration/Entry.py - The sole orchestrator for the Configuration Module.

Purpose:
This file is the public entry point for 'oaConfiguration'. It manages the 
lifecycle of the configuration manager and exports the core 'Config' 
singleton and its associated functions to the rest of the project.
"""

from .FileReaders.config_reader import Config
from .Methods.config_validator import validate_configuration
from .Methods.console_encoder import ConsoleEncoder

def get_config_instance():
    """Returns the singleton Config instance."""
    return Config()

def initialize_config(config_path="config.ini", silent=True):
    """
    Initializes the configuration from the specified path.
    """
    return Config().initialize(config_path, silent)

def validate(output_func=None):
    """
    Validates the current configuration.
    """
    return validate_configuration(output_func)

def get_encoder():
    """Returns the ConsoleEncoder for output formatting."""
    return ConsoleEncoder()

# Standardized exports
__all__ = ["Config", "get_config_instance", "initialize_config", "validate", "get_encoder"]
