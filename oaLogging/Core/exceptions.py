# oaLogging/Core/exceptions.py
# Author: Gemini (Collaborator)
# Version: 20260323.1610.1
#
# Description: Centralized Exception Classes for the OPEN-AIR System.

"""
exceptions.py - Standardized Exception Hierarchy for OPEN-AIR.

Purpose:
    Provides a consistent set of exception classes to improve error 
    reporting, observability, and diagnostic forensic trails.
"""

class OpenAirError(Exception):
    """Base class for all exceptions in the OPEN-AIR system."""
    def __init__(self, message: str, context: dict = None):
        super().__init__(message)
        self.context = context or {}

class VocalError(OpenAirError):
    """Exceptions that SHOULD be immediately logged and potentially displayed to the user."""
    pass

class ConfigurationError(VocalError):
    """Raised when system or module configuration is invalid or missing."""
    pass

class NetworkError(VocalError):
    """Raised during connectivity or communication failures (MQTT, SNMP, etc.)."""
    pass

class ProtocolError(VocalError):
    """Raised when data structure or message format deviates from the expected protocol."""
    pass

class ResourceError(VocalError):
    """Raised when required assets, files, or hardware resources are unavailable."""
    pass

class HardwareError(VocalError):
    """Raised during physical device communication failures (MIDI, VISA, etc.)."""
    pass

class CriticalModuleMissingError(ConfigurationError):
    """Raised when a mandatory system module (oa*.Entry) cannot be loaded."""
    pass

class UIConstructionError(VocalError):
    """Raised when the GUI builder fails to assemble a panel or widget."""
    pass
