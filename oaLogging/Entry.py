# oaLogging/Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260330.1030.1 # Fixed exports and removed nonexistent Logger class
#
# Description: Logging Module Entry Point.

"""
oaLogging/Entry.py - The sole orchestrator for the Logging Module.

Purpose:
This file is the public entry point for 'oaLogging'. It manages the
lifecycle of the logging system and provides access to logging utilities.
"""

# --- Core Exports ---
from .Core.logger import (
    logger,
    initialize_logging,
    set_log_directory,
    get_logger,
    debug_log,
    console_log,
    failure_log,
    SYSTEM_LOGGER,
    CORE_LOGGER,
    DATA_LOGGER,
    GUI_LOGGER,
    MQTT_LOGGER,
    SNMP_LOGGER,
    MIDI_LOGGER,
    OSC_LOGGER,
    ROUTER_LOGGER,
    FAILURE_LOGGER
)

# --- Exception Exports ---
from .Core.exceptions import (
    OpenAirError,
    VocalError,
    ConfigurationError,
    NetworkError,
    ProtocolError,
    ResourceError,
    HardwareError,
    CriticalModuleMissingError,
    UIConstructionError
)

# --- Manager Exports ---
from .Managers.log_filter_engine import LogFilterEngine

# --- Method Exports ---
from .Methods.error_handling import (
    vocal_failure_handler,
    vocal_capture
)

class LoggingEntry:
    """Entry point for logging management services."""
    def __init__(self):
        # print("📡📥📥 [INBOUND] Initializing LoggingEntry...")
        self.log_filter_engine = LogFilterEngine()

    def start(self, config=None, log_dir=None, partition="SYS"):
        """Starts the logging service."""
        if config and log_dir:
            initialize_logging(config, log_dir=log_dir, partition=partition)

    def stop(self):
        """Stops the logging service."""
        # Loguru doesn't require explicit stop for basic sinks, 
        # but if we use custom sinks with threads (like BatchLogSink),
        # we might need to handle cleanup if we had references to them.
        pass

    def status(self):
        """Returns the current status of the logging service."""
        return "active"

# Standardized exports for the Gatekeeper pattern.
__all__ = [
    "LoggingEntry",
    "logger",
    "initialize_logging",
    "set_log_directory",
    "get_logger",
    "debug_log",
    "console_log",
    "failure_log",
    "vocal_failure_handler",
    "vocal_capture",
    "OpenAirError",
    "VocalError",
    "ConfigurationError",
    "NetworkError",
    "ProtocolError",
    "ResourceError",
    "HardwareError",
    "CriticalModuleMissingError",
    "UIConstructionError",
    "LogFilterEngine",
    "SYSTEM_LOGGER",
    "CORE_LOGGER",
    "DATA_LOGGER",
    "GUI_LOGGER",
    "MQTT_LOGGER",
    "SNMP_LOGGER",
    "MIDI_LOGGER",
    "OSC_LOGGER",
    "ROUTER_LOGGER",
    "FAILURE_LOGGER"
]
