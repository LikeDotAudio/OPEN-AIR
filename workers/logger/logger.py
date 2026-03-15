# workers/logger/logger.py
#
# High-Performance Logging Framework for OPEN-AIR.
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
# Version 20260314.120000.REV01

"""
logger.py - Standardized Logging Framework for the OPEN-AIR System.

Purpose:
    Provides a high-performance, asynchronous logging abstraction layer
    based on the Loguru library. It integrates Precision Time Protocol (PTP)
    derived timestamps to ensure perfect log correlation across distributed
    system partitions (UI, Core, Hardware).

Responsibilities:
    - Configure global logging sinks (Console, Rotating File, Error Archive).
    - Patch log records with sub-millisecond TAI timestamps.
    - Provide category-bound logger instances for subsystem tracing.
    - Implement caching for configuration and time lookups to minimize
      overhead in high-frequency telemetry paths.

Constraints:
    - Requires 'workers.Showtime.ptp_time' for clock synchronization.
    - Asynchronous sinking (enqueue=True) relies on internal thread pools.
    - File-based sinks require valid write permissions in 'log_dir'.
"""

import sys
import os
from loguru import logger
from datetime import datetime
from workers.Showtime.ptp_time import get_ptp_time

# LOCAL_DEBUG: Toggles internal diagnostics for the logging system.
LOCAL_DEBUG = True

# --- Global State and Caches ---
# These variables cache expensive lookups to ensure negligible overhead.
_config_instance_cache = None
_last_ptp_second = -1
_cached_hhmmss = ""

def _get_cached_config():
    """
    Retrieves the application configuration singleton with local caching.

    Lead with action: Fetches the 'Config' instance to determine verbosity
    and feature flags. Uses a local cache to avoid redundant singleton
    accesses during early boot phases.

    Inputs:
        None.

    Outputs:
        Config: The active configuration instance, or a 'DummyConfig' fallback.
    """
    global _config_instance_cache
    if _config_instance_cache:
        return _config_instance_cache
    
    try:
        from managers.configini.config_reader import Config
        if Config._instance:
            _config_instance_cache = Config._instance
            return _config_instance_cache
    except ImportError:
        pass
    
    # Fallback to allow logging before the configuration system is online.
    class DummyConfig:
        ENABLE_DEBUG_MODE = True
        ENABLE_DEBUG_SCREEN = True
        global_settings = {"debug_enabled": True}
    return DummyConfig()

def ptp_patcher(record):
    """
    Instruments log records with high-precision PTP (TAI) timestamps.

    Lead with action: Injects a formatted 'ptp_time' string into the Loguru
    extra context. Employs a time-caching strategy to minimize 'strftime' calls.

    Inputs:
        record (dict): The Loguru internal record to be modified in-place.
    """
    global _last_ptp_second, _cached_hhmmss
    
    ptp_now = get_ptp_time()
    current_second = int(ptp_now)
    
    # Cache the HHMMSS string and only update when the integer second changes.
    if current_second != _last_ptp_second:
        dt = datetime.fromtimestamp(ptp_now)
        _cached_hhmmss = dt.strftime("%H%M%S")
        _last_ptp_second = current_second
    
    # Append milliseconds using fast f-string formatting.
    ms = int((ptp_now - current_second) * 1000)
    record["extra"]["ptp_time"] = f"{_cached_hhmmss}.{ms:03d}"

def initialize_logging(config, log_dir=None, partition="SYS"):
    """
    Configures the global Loguru infrastructure and sinks.

    Lead with action: Clears default handlers and instantiates custom sinks
    for the console and filesystem based on the provided configuration.

    Inputs:
        config (Config): The application configuration object.
        log_dir (str, optional): The base directory for log persistence.
        partition (str): The logical system partition identifier.

    Outputs:
        None.
    """
    # Configure global defaults for the 'extra' dictionary.
    logger.configure(
        patcher=ptp_patcher,
        extra={"category": "SYSTEM", "partition": partition}
    )
    
    # Remove existing handlers to avoid duplicate output.
    logger.remove()

    debug_enabled = config.global_settings.get("debug_enabled", False)
    
    # Primary format for colorized terminal output.
    log_format = (
        "<green>{extra[ptp_time]}</green>|"
        "<level>{level: <8}</level>|"
        "<yellow>{extra[partition]: <4}</yellow>|"
        "<magenta>{extra[category]: <10}</magenta>|"
        "<cyan>{name: <20}</cyan>|"
        "<level>{message}</level>"
    )
    
    # Simplified format for disk-based log files.
    file_format = (
        "{extra[ptp_time]} | {level: <8} | {extra[partition]: <4} | "
        "{extra[category]: <10} | {name: <20} | {message}"
    )

    # 1. --- Console Sink ---
    console_level = "TRACE" if debug_enabled else "INFO"
    logger.add(
        sys.stderr, 
        format=log_format, 
        level=console_level,
        enqueue=True,
        filter=lambda record: record["extra"].get("category") != "QUARANTINE",
        diagnose=False
    )

    if not log_dir:
        return

    # 2. --- Filesystem Sinks ---
    try:
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        
        # Primary Application Log (Rotating).
        file_level = "DEBUG" if debug_enabled else "INFO"
        logger.add(
            os.path.join(log_dir, f"Application_{timestamp}.log"),
            format=file_format, level=file_level, enqueue=True,
            rotation="20 MB", retention="1 month",
            filter=lambda record: record["extra"].get("category") != "QUARANTINE",
            backtrace=True, diagnose=False
        )

        # Isolated Error Log (High Severity).
        logger.add(
            os.path.join(log_dir, f"errors_{timestamp}.log"),
            format=file_format, level="WARNING", backtrace=True,
            diagnose=True, enqueue=True, rotation="10 MB"
        )

    except Exception as e:
        print(f"CRITICAL: Logging filesystem initialization failed: {e}", 
              file=sys.stderr)

def set_log_directory(directory: str, partition="SYS"):
    """
    Simplified entry point for directory-based logging initialization.

    Inputs:
        directory (str): The target path for log files.
        partition (str): The logical partition name.
    """
    c = _get_cached_config()
    initialize_logging(c, log_dir=directory, partition=partition)

def get_logger(category="SYSTEM"):
    """
    Returns a bound logger instance for a specific subsystem.

    Inputs:
        category (str): The subsystem identifier (e.g., 'MQTT').
    """
    return logger.bind(category=category)

# --- Subsystem-Specific Bound Instances ---
builder_logger = logger.bind(category="BUILDER")
gui_logger     = logger.bind(category="GUI")
comm_logger    = logger.bind(category="COMM")
core_logger    = logger.bind(category="CORE")
data_logger    = logger.bind(category="DATA")
visa_logger    = logger.bind(category="VISA")
yak_logger     = logger.bind(category="YAK")
mqtt_logger    = logger.bind(category="MQTT")
router_logger  = logger.bind(category="ROUTER")
quarantine_logger = logger.bind(category="QUARANTINE")

def debug_logger(message: str, *args, **kwargs):
    """Legacy compatibility wrapper for debug logging."""
    logger.opt(depth=1).bind(category="SYSTEM").debug(message, *args)

def console_log(message: str):
    """Routes informational messages to the primary system log."""
    logger.opt(depth=1).bind(category="SYSTEM").info(message)

# Standard aliases for cross-module compatibility.
debug_log = debug_logger
