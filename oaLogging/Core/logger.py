# Core/logger.py
# Author: Anthony Peter Kuzub
# Version: 20260323.1600.1
#
# Description: High-Performance Logging Framework for OPEN-AIR.

"""
logger.py - Standardized Logging Framework for the OPEN-AIR System.

Purpose:
    Provides a high-performance, asynchronous logging abstraction layer
    based on the Loguru library. It integrates Precision Time Protocol (PTP)
    derived timestamps to ensure perfect log correlation across distributed
    system partitions (UI, Core, Hardware).

Responsibilities:
    - Configure global logging sinks (Console, Rotating File, Error Archive, JSON Lines).
    - Patch log records with high-precision TAI timestamps derived from PTP.
    - Provide category-bound logger instances with emoji prefixes for subsystem tracing.
    - Implement caching for configuration and time lookups to minimize
      overhead in high-frequency telemetry paths.

Constraints:
    - Requires 'oaGuiShowtime.ptp_time' for clock synchronization.
    - Asynchronous sinking (enqueue=True) relies on internal thread pools.
    - File-based sinks require valid write permissions in 'log_dir'.
"""

import sys
import os
import threading
import time
from collections import deque
from loguru import logger
from datetime import datetime
from oaLogging.Constants.subsystem_emojis import SUBSYSTEM_EMOJIS

try:
    from oaGuiShowtime.Methods.ptp_time import get_ptp_time
except ImportError:
    # Fallback for when ptp_time might not be available during early init
    def get_ptp_time():
        return time.time()

# --- Global State and Caches ---
_config_instance_cache = None
_last_ptp_second = -1
_cached_hhmmss = ""

def get_emoji(key: str) -> str:
    """Safely retrieves an emoji for a given key, defaulting to a generic one."""
    return SUBSYSTEM_EMOJIS.get(key.upper(), "❓")

class BatchLogSink:
    """
    ⚡ HIGH PERFORMANCE SINK: Caches logs in memory and writes in batches.
    Reduces I/O overhead and lock contention on the hot path.
    """
    def __init__(self, file_path, format_str, batch_size=50, interval=2):
        self.file_path = file_path
        self.format_str = format_str
        self.batch_size = batch_size
        self.interval = interval
        self.buffer = deque()
        self._lock = threading.RLock() # ⚡ FIX: Use RLock to prevent deadlock on flush
        self._is_running = True
        
        # Start the background flusher thread.
        self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True, name=f"LogBatchFlusher-{os.path.basename(file_path)}")
        self._flush_thread.start()

    def write(self, message):
        """Standard Loguru sink write method."""
        with self._lock:
            self.buffer.append(message)
            if len(self.buffer) >= self.batch_size:
                self._trigger_flush()

    def _trigger_flush(self):
        """Internal helper to write the buffer to disk."""
        if not self.buffer:
            return
            
        # Swap buffer to minimize lock time
        with self._lock:
            lines_to_write = list(self.buffer)
            self.buffer.clear()
            
        try:
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.writelines(lines_to_write)
        except Exception as e:
            # This critical error should always be visible
            print(f"CRITICAL: Log batch write to {self.file_path} failed: {e}", file=sys.stderr)

    def _flush_loop(self):
        """Background thread to ensure logs are flushed periodically."""
        while self._is_running:
            try:
                time.sleep(self.interval)
                self._trigger_flush()
            except Exception as e:
                print(f"CRITICAL: Log flush loop error for {self.file_path}: {e}", file=sys.stderr)

    def stop(self):
        """Stops the flusher thread and flushes remaining logs."""
        self._is_running = False
        self._trigger_flush()

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
        from oaConfiguration.FileReaders.config_reader import Config
        if Config._instance:
            _config_instance_cache = Config._instance
            return _config_instance_cache
    except ImportError:
        pass
    
    # Fallback to allow logging before the configuration system is fully online.
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
    for the console, filesystem (application & error), and JSON Lines
    based on the provided configuration.

    Inputs:
        config (Config): The application configuration object.
        log_dir (str, optional): The base directory for log persistence.
        partition (str): The logical system partition identifier.

    Outputs:
        None.
    """
    # Ensure partition has an emoji prefix if available
    partition_with_emoji = f"{get_emoji(partition)} {partition}"

    # Configure global defaults for the 'extra' dictionary.
    logger.configure(
        patcher=ptp_patcher,
        extra={"category": "SYSTEM", "partition": partition_with_emoji}
    )
    
    # Remove existing handlers to avoid duplicate output.
    logger.remove()

    debug_enabled = config.global_settings.get("debug_enabled", False)
    console_level = "TRACE" if debug_enabled else "INFO"
    file_level = "TRACE" if debug_enabled else "INFO"
    
    # --- Log Formats ---
    # Primary format for colorized terminal output. Includes emojis for partition and category.
    log_format_console = (
        "<green>{extra[ptp_time]}</green>|"
        "<level>{level: <8}</level>|"
        "<yellow>{extra[partition]: <9}</yellow>|"
        "<magenta>{extra[category]: <18}</magenta>|"
        "<cyan>{name: <20}</cyan>|"
        "<level>{message}</level>"
    )
    
    # Simplified format for disk-based log files.
    file_format_plain = (
        "{extra[ptp_time]} | {level: <8} | {extra[partition]: <9} | "
        "{extra[category]: <18} | {name: <20} | {message}"
    )
    
    # JSON Lines format for structured logging.
    jsonl_format = (
        '{"timestamp": "{extra[ptp_time]}", "level": "{level}", "partition": "{extra[partition]}", '
        '"category": "{extra[category]}", "name": "{name}", "message": "{message}", '
        '"process_id": "{process}", "thread_id": "{thread}"}'
    )

    # 1. --- Console Sink ---
    logger.add(
        sys.stderr, 
        format=log_format_console, 
        level=console_level,
        enqueue=False, # ⚡ OPTIMIZATION: Direct write to stderr
        filter=lambda record: record["extra"].get("category") != "🚫 QUARANTINE",
        diagnose=False
    )

    if not log_dir:
        return

    # --- Ensure Log Directory Exists ---
    try:
        os.makedirs(log_dir, exist_ok=True)
        run_log_dir = os.path.join(log_dir, "ApplicationRunLog")
        error_log_dir = os.path.join(log_dir, "Errors")
        jsonl_log_dir = os.path.join(log_dir, "JsonLines")
        
        os.makedirs(run_log_dir, exist_ok=True)
        os.makedirs(error_log_dir, exist_ok=True)
        os.makedirs(jsonl_log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        
        # 2. --- Application Log Sink ---
        app_log_path = os.path.join(run_log_dir, f"Application_{timestamp}.log")
        logger.add(
            BatchLogSink(app_log_path, format_str=file_format_plain, batch_size=50, interval=2),
            format=file_format_plain, level=file_level,
            filter=lambda record: record["extra"].get("category") != "🚫 QUARANTINE",
            backtrace=True, diagnose=True
        )

        # 3. --- Isolated Error Log Sink ---
        error_log_path = os.path.join(error_log_dir, f"errors_{timestamp}.log")
        logger.add(
            BatchLogSink(error_log_path, format_str=file_format_plain, batch_size=10, interval=2),
            format=file_format_plain, level="WARNING",
            filter=lambda record: record["extra"].get("category") != "🚫 QUARANTINE",
            backtrace=True, diagnose=True
        )
        
        # 4. --- JSON Lines Sink ---
        jsonl_log_path = os.path.join(jsonl_log_dir, f"structured_{timestamp}.jsonl")
        logger.add(
            jsonl_log_path,
            format=jsonl_format,
            level="TRACE" if debug_enabled else "INFO",
            filter=lambda record: record["extra"].get("category") != "🚫 QUARANTINE",
            rotation="10 MB",
            compression="zip",
            catch=True
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

def get_logger(category: str, emoji_prefix: str = None):
    """
    Returns a bound logger instance for a specific subsystem, ensuring emoji prefix.

    Inputs:
        category (str): The subsystem identifier (e.g., 'MQTT').
        emoji_prefix (str, optional): Explicit emoji to use. If None, uses mapping.
    """
    emoji = emoji_prefix if emoji_prefix else get_emoji(category)
    padded_category = f"{emoji} {category}".ljust(18)[:18] 
    return logger.bind(category=padded_category)

# --- Subsystem-Specific Bound Instances ---
SYSTEM_LOGGER    = get_logger("SYSTEM")
CONFIG_LOGGER    = get_logger("CONFIG")
DEPLOY_LOGGER    = get_logger("DEPLOY")
PIPELINE_LOGGER  = get_logger("PIPELINE")

SENSOR_LOGGER    = get_logger("SENSOR")
POWER_LOGGER     = get_logger("POWER")
THERMAL_LOGGER   = get_logger("THERMAL")
SERVERLESS_LOGGER= get_logger("SERVERLESS")

INBOUND_LOGGER   = get_logger("INBOUND")
OUTBOUND_LOGGER  = get_logger("OUTBOUND")
SCRAPER_LOGGER   = get_logger("SCRAPER")
STREAM_LOGGER    = get_logger("STREAM")

BUILDER_LOGGER   = get_logger("BUILDER")
GUI_LOGGER       = get_logger("GUI")
RENDER_LOGGER    = get_logger("RENDER")
ACTION_LOGGER    = get_logger("ACTION")
ANALYTICS_LOGGER = get_logger("ANALYTICS")
MOBILE_LOGGER    = get_logger("MOBILE")
BROWSER_LOGGER   = get_logger("BROWSER")
LAYOUT_LOGGER    = get_logger("LAYOUT")

AI_ML_LOGGER     = get_logger("AI/ML")
COMPUTE_LOGGER   = get_logger("COMPUTE")
LOOP_LOGGER      = get_logger("LOOP")
BRANCH_LOGGER    = get_logger("BRANCH")

LAUNCHING_LOGGER = get_logger("LAUNCHING")
SWEEPING_LOGGER  = get_logger("SWEEPING")
FILE_IO_LOGGER   = get_logger("FILE_IO")
MEM_LEAK_LOGGER  = get_logger("MEM_LEAK")

COMM_LOGGER      = get_logger("COMM")
CORE_LOGGER      = get_logger("CORE")
DATA_LOGGER      = get_logger("DATA")
VISA_LOGGER      = get_logger("VISA")
YAK_LOGGER       = get_logger("YAK")
MQTT_LOGGER      = get_logger("MQTT")
SNMP_LOGGER      = get_logger("SNMP")
MIDI_LOGGER      = get_logger("MIDI")
OSC_LOGGER       = get_logger("OSC")
ROUTER_LOGGER    = get_logger("ROUTER")
QUARANTINE_LOGGER= get_logger("QUARANTINE")
TABLE_LOGGER     = get_logger("TABLE")
CACHE_LOGGER     = get_logger("CACHE")
LAYER_LOGGER     = get_logger("LAYER")
FACTORY_LOGGER   = get_logger("FACTORY")
PARSER_LOGGER    = get_logger("PARSER")
FAILURE_LOGGER   = get_logger("FAILURE")

# Legacy aliases for compatibility
builder_logger = BUILDER_LOGGER
gui_logger     = GUI_LOGGER
comm_logger    = COMM_LOGGER
core_logger    = CORE_LOGGER
data_logger    = DATA_LOGGER
visa_logger    = VISA_LOGGER
yak_logger     = YAK_LOGGER
mqtt_logger    = MQTT_LOGGER
snmp_logger    = SNMP_LOGGER
midi_logger    = MIDI_LOGGER
osc_logger     = OSC_LOGGER
router_logger  = ROUTER_LOGGER
layout_logger  = LAYOUT_LOGGER
table_logger   = TABLE_LOGGER
cache_logger   = CACHE_LOGGER
layer_logger   = LAYER_LOGGER
factory_logger = FACTORY_LOGGER
parser_logger  = PARSER_LOGGER
quarantine_logger = QUARANTINE_LOGGER
failure_logger = FAILURE_LOGGER

def debug_logger(message: str, *args, **kwargs):
    """Legacy compatibility wrapper for debug logging."""
    logger.opt(depth=1).bind(category=f"{get_emoji('SYSTEM')} SYSTEM").debug(message, *args)

def console_log(message: str):
    """Routes informational messages to the primary system log."""
    logger.opt(depth=1).bind(category=f"{get_emoji('SYSTEM')} SYSTEM").info(message)

def failure_log(message: str, *args, **kwargs):
    """Routes critical failure messages to the primary system log with maximal impact."""
    logger.opt(depth=1).bind(category=f"{get_emoji('FAILURE')} FAILURE").error(message, *args)

# Standard aliases for cross-module compatibility.
debug_log = debug_logger
