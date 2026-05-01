# oaLogging/Core/logger.py
# Author: Anthony Peter Kuzub
# Version: 20260413.1000.1
#
# Description: High-Performance Logging Framework for OPEN-AIR.

"""
logger.py - Standardized Logging Framework for the OPEN-AIR System.

Purpose:
    Provides a high-performance, asynchronous logging abstraction layer
    based on the Loguru library. It integrates Precision Time Protocol (PTP)
    derived timestamps to ensure perfect log correlation across distributed
    system partitions (UI, Core, Hardware).
"""

import os
import sys
from datetime import datetime

from loguru import logger

from oaLogging.Constants.logging_constants import (
    APP_LOG_BATCH_SIZE,
    APP_LOG_INTERVAL,
    COMMS_ELEMENTS,
    ERROR_LOG_BATCH_SIZE,
    ERROR_LOG_INTERVAL,
    FILE_FORMAT_PLAIN,
    JSONL_FORMAT,
    LOG_FORMAT_CONSOLE,
    PROTOCOL_LOG_BATCH_SIZE,
    PROTOCOL_LOG_INTERVAL,
    PROTOCOLS,
    TEST_LOG_BATCH_SIZE,
    TEST_LOG_INTERVAL,
)

# --- Constants ---
from oaLogging.Constants.subsystem_emojis import SUBSYSTEM_EMOJIS
from oaLogging.Core.rust_sink_bridge import teardown_rust_sink

# --- Methods and Helpers ---
from oaLogging.Methods.config_retrieval import _get_cached_config
from oaLogging.Methods.log_filters import rust_gate_filter
from oaLogging.Methods.log_patchers import ptp_patcher

# --- Sinks and Bridges ---
from oaLogging.Workers.batch_sink import BatchLogSink


def get_emoji(key: str) -> str:
    """Safely retrieves an emoji for a given key, defaulting to a generic one."""
    return SUBSYSTEM_EMOJIS.get(key.upper(), "❓")

def shutdown_logging():
    """
    Safely shuts down the logging system, flushing all asynchronous sinks.
    """
    logger.remove()
    teardown_rust_sink()

def initialize_logging(config, log_dir=None, partition="SYS"):
    """
    Configures the global Loguru infrastructure and sinks.
    """
    # Ensure partition has an emoji prefix if available
    partition_with_emoji = f"{get_emoji(partition)} {partition}"

    # Configure global defaults for the 'extra' dictionary.
    logger.configure(
        patcher=ptp_patcher,
        extra={"category": "SYSTEM", "partition": partition_with_emoji, "protocol": None}
    )

    # Remove existing handlers to avoid duplicate output.
    logger.remove()

    debug_enabled = config.global_settings.get("debug_enabled", False)
    console_level = "TRACE" if debug_enabled else "INFO"
    file_level = "TRACE" if debug_enabled else "INFO"

    # ⚡ PARTITION MUTING
    if hasattr(config, "DEBUG_MATRIX"):
        partition_toggle = config.DEBUG_MATRIX.get(f"SYS_{partition.upper()}")
        if partition_toggle is False:
            console_level = "WARNING"

    # --- Log Formats ---
    show_ts = config.global_settings.get("timestamp_logs", True)
    ts_fmt = "<green>{extra[ptp_time]}</green>|" if show_ts else ""
    log_format_console = f"{ts_fmt}{LOG_FORMAT_CONSOLE}"

    ts_fmt_plain = "{extra[ptp_time]} | " if show_ts else ""
    file_format_plain = f"{ts_fmt_plain}{FILE_FORMAT_PLAIN}"

    jsonl_format = JSONL_FORMAT

    # 1. --- Console Sink ---
    logger.add(
        sys.stderr,
        format=log_format_console,
        level=console_level,
        enqueue=False,
        filter=rust_gate_filter,
        diagnose=False
    )

    if not log_dir:
        return

    # --- Ensure Log Directory Exists ---
    try:
        os.makedirs(log_dir, exist_ok=True)
        run_log_dir = os.path.join(log_dir, "ApplicationRunLog")
        error_log_dir = os.path.join(log_dir, "Errors")
        comms_log_dir = os.path.join(log_dir, "Comms")
        gui_log_dir = os.path.join(log_dir, "Gui")

        os.makedirs(run_log_dir, exist_ok=True)
        os.makedirs(error_log_dir, exist_ok=True)
        os.makedirs(comms_log_dir, exist_ok=True)
        os.makedirs(gui_log_dir, exist_ok=True)

        # 2. --- Application Log Sink ---
        app_log_pattern = os.path.join(run_log_dir, "Application_{time}.log")
        logger.add(
            BatchLogSink(app_log_pattern, format_str=file_format_plain, batch_size=APP_LOG_BATCH_SIZE, interval=APP_LOG_INTERVAL),
            format=file_format_plain, level=file_level,
            filter=rust_gate_filter,
            backtrace=True, diagnose=True
        )

        # 3. --- Dedicated GUI/Render Log Sink ---
        gui_log_pattern = os.path.join(gui_log_dir, "GuiRender_{time}.log")
        
        def gui_filter(record):
            # 1. Filter by Module Name
            module_name = record["name"]
            if any(m in module_name for m in ["oaGui", "oaGuiElements", "oaGuiEditorWYSIWYG"]):
                return rust_gate_filter(record)
            
            # 2. Filter by Category
            category = record["extra"].get("category", "").upper()
            gui_keywords = ["GUI", "RENDER", "LAYOUT", "WYSIWYG", "BUILDER"]
            if any(kw in category for kw in gui_keywords):
                return rust_gate_filter(record)
                
            return False

        logger.add(
            BatchLogSink(gui_log_pattern, format_str=file_format_plain, batch_size=PROTOCOL_LOG_BATCH_SIZE, interval=PROTOCOL_LOG_INTERVAL),
            format=file_format_plain, level=file_level,
            filter=gui_filter,
            backtrace=True, diagnose=True
        )

        # 4. --- Isolated Error Log Sink ---
        error_log_pattern = os.path.join(error_log_dir, "errors_{time}.log")
        logger.add(
            BatchLogSink(error_log_pattern, format_str=file_format_plain, batch_size=ERROR_LOG_BATCH_SIZE, interval=ERROR_LOG_INTERVAL),
            format=file_format_plain, level="WARNING",
            filter=rust_gate_filter,
            backtrace=True, diagnose=True
        )

        # 4. --- Protocol and Broker Segregated Sinks ---
        for proto in PROTOCOLS:
            proto_dir = os.path.join(comms_log_dir, proto)
            os.makedirs(proto_dir, exist_ok=True)
            proto_pattern = os.path.join(proto_dir, f"{proto}_{{time}}.log")

            # Use a closure for the filter to correctly capture 'proto'
            def make_filter(p):
                return lambda record: record["extra"].get("protocol") == p and rust_gate_filter(record)

            logger.add(
                BatchLogSink(proto_pattern, format_str=file_format_plain, batch_size=PROTOCOL_LOG_BATCH_SIZE, interval=PROTOCOL_LOG_INTERVAL),
                format=file_format_plain, level=file_level,
                filter=make_filter(proto),
                backtrace=True, diagnose=True
            )

    except Exception as e:
        print(f"CRITICAL: Logging filesystem initialization failed: {e}", file=sys.stderr)

def set_log_directory(directory: str, partition="SYS"):
    """Simplified entry point for directory-based logging initialization."""
    c = _get_cached_config()
    initialize_logging(c, log_dir=directory, partition=partition)

def initialize_test_logging(log_dir: str):
    """Configures a dedicated sink for test run logs."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_log_path = os.path.join(log_dir, f"TestRun_{timestamp}.log")

    file_format_plain = "{extra[ptp_time]} | " + FILE_FORMAT_PLAIN

    logger.configure(
        patcher=ptp_patcher,
        extra={"partition": "🧪 TEST", "category": "TEST"}
    )

    logger.add(
        BatchLogSink(test_log_path, format_str=file_format_plain, batch_size=TEST_LOG_BATCH_SIZE, interval=TEST_LOG_INTERVAL),
        format=file_format_plain, level="TRACE",
        filter=lambda record: "TEST" in record["extra"].get("category", ""),
        backtrace=True, diagnose=True
    )

    return test_log_path

def get_logger(category: str, emoji_prefix: str = None):
    """Returns a bound logger instance for a specific subsystem."""
    if emoji_prefix is None and category.upper() in COMMS_ELEMENTS:
        emoji = "📡"
        cat_name = f"COMM: {category.upper()}"
    else:
        emoji = emoji_prefix if emoji_prefix else get_emoji(category)
        cat_name = category.upper()

    full_category = f"{emoji} {cat_name}"
    padded_category = full_category.ljust(18)
    return logger.bind(category=padded_category)

# --- Subsystem-Specific Bound Instances ---
SYSTEM_LOGGER    = get_logger("SYSTEM")
CONFIG_LOGGER    = get_logger("CONFIG")
DEPLOY_LOGGER    = get_logger("DEPLOY")
PIPELINE_LOGGER  = get_logger("PIPELINE")
TEST_LOGGER      = get_logger("TEST")

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
WYSIWYG_LOGGER   = get_logger("WYSIWYG")

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
SMPTE2138_LOGGER    = get_logger("SMPTE2138")
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
wysiwyg_logger = WYSIWYG_LOGGER
parser_logger  = PARSER_LOGGER
test_logger    = TEST_LOGGER
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

# --- Matrix-Aware Logging APIs ---
