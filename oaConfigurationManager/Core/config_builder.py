# Core/config_builder.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

"""
config_builder.py - Default Configuration Generator for OPEN-AIR.

Purpose:
This module provides a mechanism to generate a default 'config.ini' file 
containing the necessary settings for the OPEN-AIR system to function. 
It ensures that even in the absence of a pre-existing configuration, 
the system has sensible defaults to fall back on.

Primary Responsibilities:
- Define the default structure and values for the system configuration.
- Write the configuration to a specified filesystem path using a 
  comment-rich template.

Assumptions and Constraints:
- Assumes the caller has write permissions to the destination directory.
- Requires the 'pathlib' module.
- The generated file follows the standard INI format.
"""

import pathlib


def create_default_config_ini(config_path: pathlib.Path, silent: bool = False):
    """
    Creates a default config.ini file with predefined settings and descriptive comments.

    Parameters:
        config_path (pathlib.Path): The absolute or relative path where the 
            config.ini file should be created. Must be a valid path object.
        silent (bool): If True, suppresses all console output during the 
            creation process. Defaults to False.
    """
    config_content = """# OPEN-AIR Configuration File
# This file controls the behavior of the core system, debugging, and communication protocols.

[UI]
# Percentage split for the main UI layout
layout_split_equal = 50
# Total weight for full-screen layout calculations
layout_full_weight = 100
# If True, shows a notification when the config file is reloaded
reload_config_displayed = False

[Version]
# The current system version (Format: YYYYMMDD)
current_version = 20260406

[System]
# The primary interface language
language_selection = En
# If True, network ports will be randomized to allow multiple instances.
randomize_ports = True

[Debug]
# Global master toggle for debug mode
enable_debug_mode = True
# Display debug info on the application screen
enable_debug_screen = True
# Toggle background file logging to /oaDataLogs
enable_log_to_file = True

[DEBUG_MATRIX]
master_debug_enable = True
enable_log_to_file = True

# Master Partition Toggles - Set to False to mute entire process output (except ERRORS)
sys_sup = True
sys_core = True
sys_ui = True
sys_gui = True
sys_comms = True
sys_data = True
sys_router = True
element_mqtt = True
element_snmp = True
element_osc = True
element_rest = True
element_aes70 = True
element_midi = True

[DEBUG_CORE_ORCHESTRATION]
sys_orchestration = True
sys_watchdog = True
sys_ptp = True
sys_taskpool = True
sys_audio = True

[DEBUG_STATE_DATA]
data_state_cache = True
data_splinker = True
data_audits = True

[DEBUG_FILE_IO]
file_import = True
file_export = True

[DEBUG_TRANSLATOR]
trans_yak = True
trans_manifest = True
trans_state_mirror = True
trans_visa = True


[DEBUG_COMMS_PROTOCOLS]
comms_mqtt = True
comms_osc = True
comms_aes70 = True
comms_smpte2138 = True
comms_snmp = True
comms_midi = True
comms_rest = True
comms_ember = True
comms_visa = True
comms_broker = True


[DEBUG_GUI]
gui_manager = True
gui_builder = True
gui_elements = True
gui_style = True
gui_telemetry = True

[DEBUG_RUST_FFI]
rust_trie_search = True
rust_disk_flusher = True
rust_pattern_engine = True
rust_st2138_codec = True

[DEBUG_ROUTER]
# Controls specific log groups within the Protocol Router
router_ingest = True
router_dispatch = True
router_settle = True
router_failover = True

# Function Level Exclusions/Inclusions (Comma separated)
# Functions listed here will have their logs suppressed
mute_functions = 
#update_canvas, poll_buffer, heart_beat

# Functions listed here will always log, regardless of other debug states
force_functions = 

[MQTT]
# IP address or hostname of the MQTT Broker
broker_address = localhost
# Port for the MQTT Broker (Default: 1883)
broker_port = 1883
# Authentication credentials
mqtt_username = guest
mqtt_password = guest
# Persistent message behavior
mqtt_retain_behavior = True

[ScanSettings]
# Toggle automatic discovery for different hardware and protocols
scan_gateways = True
scan_usb = True
scan_ip_direct = True
scan_aes70 = True
scan_osc = True
scan_snmp = True

[OSC]
# Listening port for incoming OSC messages
osc_rx_port = 8000
# Destination port for outgoing OSC messages
osc_tx_port = 9000
# Destination IP address for OSC commands
osc_remote_ip = 127.0.0.1

[REST]
# Host interface for the REST API (0.0.0.0 to listen on all interfaces)
rest_host = 0.0.0.0
# Port for the REST API server
rest_port = 44845
# Cross-Origin Resource Sharing (CORS) allowed origins (* for all)
rest_cors_origins = *
"""

    with open(config_path, "w") as configfile:
        configfile.write(config_content)

    if not silent:
        print(f"📡📤📤 [CONFIG] Created default config.ini at {config_path}")
