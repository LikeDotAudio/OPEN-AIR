"""
oaOchestration/Entry.py - The sole orchestrator for the Orchestration Module.

Purpose:
This file is the public entry point for 'oaOchestration'. It manages 
the system-wide initialization sequence, path setup, and core 
bootstrapping logic.
"""

from .Managers.application_initializer import initialize_app
from .Managers.path_initializer import initialize_paths
from .Constants import project_paths as paths
from .Methods.debug_cleaner import clear_debug_logs
from .Methods.json_validator import validate_json

def start_system_orchestration():
    """
    Orchestrates the initial setup sequence of the application.
    """
    initialize_paths()
    return initialize_app()

def get_paths():
    """Returns the project paths constant object."""
    return paths

# Standardized exports
__all__ = [
    "initialize_app", 
    "initialize_paths", 
    "paths", 
    "clear_debug_logs", 
    "validate_json",
    "start_system_orchestration",
    "get_paths"
]
