# oaLogging/Constants/logging_constants.py
# Author: Gemini (Collaborator)
# Version: 20260413.1000.1
#
# Description: Centralized constants for the OPEN-AIR Logging Module.

# --- Log Formats ---
# Primary format for colorized terminal output.
# Note: {ts_fmt} is dynamically prepended in initialize_logging.
LOG_FORMAT_CONSOLE = (
    "<level>{level: <8}</level>|"
    "<yellow>{extra[partition]: <9}</yellow>|"
    "<magenta>{extra[category]: <18}</magenta>|"
    "<cyan>{name: <20}</cyan>|"
    "<level>{message}</level>"
)

# Simplified format for disk-based log files.
# Note: {ts_fmt_plain} is dynamically prepended in initialize_logging.
FILE_FORMAT_PLAIN = (
    "{level: <8} | {extra[partition]: <9} | "
    "{extra[category]: <18} | {name: <20} | {message}"
)

# JSON Lines format for structured logging.
JSONL_FORMAT = (
    '{{"timestamp": "{extra[ptp_time]}", "level": "{level}", "partition": "{extra[partition]}", '
    '"category": "{extra[category]}", "name": "{name}", "message": "{message}", '
    '"process_id": "{process}", "thread_id": "{thread}"}}'
)

# --- Subsystem Categorization ---
# Elements that should always be treated as communications and use the 📡 emoji.
COMMS_ELEMENTS = {
    "MQTT", "OSC", "MIDI", "SNMP", "VISA", "AES70", "REST",
    "EMBER", "SMPTE2138", "ROUTER", "BROKER", "COMM", "COMMS"
}

# Protocols that receive segregated log sinks.
PROTOCOLS = [
    "OSC", "MIDI", "MQTT", "SNMP", "VISA", "AES70", "REST",
    "EMBER", "SMPTE2138", "BROKER", "GUI", "WYSIWYG"
]

# --- Batch Sink Configurations ---
# Default settings for BatchLogSink instances.
DEFAULT_BATCH_SIZE = 50
DEFAULT_FLUSH_INTERVAL = 2

# Specialized batch settings for different log types.
APP_LOG_BATCH_SIZE = 50
APP_LOG_INTERVAL = 2

ERROR_LOG_BATCH_SIZE = 10
ERROR_LOG_INTERVAL = 2

PROTOCOL_LOG_BATCH_SIZE = 20
PROTOCOL_LOG_INTERVAL = 2

TEST_LOG_BATCH_SIZE = 1
TEST_LOG_INTERVAL = 1
