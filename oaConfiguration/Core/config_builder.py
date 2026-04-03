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

[Version]
# The current system version (Format: YYYYMMDD)
current_version = 20251225

[Debug]
# Global master toggle for debug mode
enable_debug_mode = True
# Display debug info on the application screen
enable_debug_screen = True
# Toggle background file logging to /oaDataLogs
enable_log_to_file = True

[DEBUG_MATRIX]
# Global Killswitch - If True, overrides all other debug settings
master_debug_enable = False

# System Level Toggles - Enable tracing for specific subsystems
sys_comms = False
sys_gui = False
sys_data = False
sys_router = False
sys_core = False

# Element Level Overrides - Fine-grained control for specific protocol modules
element_mqtt = False
element_snmp = False
element_midi = False
element_osc = False
element_aes70 = False
element_rest = False
element_gui_builder = False

# Function Level Exclusions/Inclusions (Comma separated)
# Functions listed here will have their logs suppressed
mute_functions = update_canvas, poll_buffer, heart_beat
# Functions listed here will always log, regardless of other debug states
force_functions = initialize_connection, critical_state_change

[UI]
# Percentage split for the main UI layout
layout_split_equal = 50
# Total weight for full-screen layout calculations
layout_full_weight = 100
# If True, shows a notification when the config file is reloaded
reload_config_displayed = False

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
