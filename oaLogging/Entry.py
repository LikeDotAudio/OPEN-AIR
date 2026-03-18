"""
oaLogging/Entry.py - The sole orchestrator for the Logging Module.

Purpose:
This file is the public entry point for 'oaLogging'. It manages the 
initialization of the system-wide logging framework and exports 
logging utilities to the project.
"""

from .Managers.logger import (
    initialize_logging, 
    get_logger, 
    quarantine_logger,
    BatchLogSink
)
from .Managers.log_filter_engine import LogFilterEngine

def start_logging(log_dir=None, rotation="500 MB", retention="10 days"):
    """
    Initializes the system-wide logging sink.
    """
    return initialize_logging(log_dir, rotation, retention)

def get_module_logger(name):
    """
    Returns a logger instance bound to the specified module name.
    """
    return get_logger(name)

# Standardized exports
__all__ = [
    "initialize_logging", 
    "get_logger", 
    "quarantine_logger", 
    "BatchLogSink",
    "LogFilterEngine",
    "start_logging",
    "get_module_logger"
]
