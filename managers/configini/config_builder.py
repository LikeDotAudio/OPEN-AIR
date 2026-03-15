"""
config_builder.py - Default Configuration Generator for OPEN-AIR.

Purpose:
This module provides a mechanism to generate a default 'config.ini' file 
containing the necessary settings for the OPEN-AIR system to function. 
It ensures that even in the absence of a pre-existing configuration, 
the system has sensible defaults to fall back on.

Primary Responsibilities:
- Define the default structure and values for the system configuration.
- Write the configuration to a specified filesystem path.

Assumptions and Constraints:
- Assumes the caller has write permissions to the destination directory.
- Requires the 'configparser' and 'pathlib' modules.
- The generated file follows the standard INI format.
"""

import configparser
import pathlib


def create_default_config_ini(config_path: pathlib.Path, silent: bool = False):
    """
    Creates a default config.ini file with predefined settings.

    Parameters:
        config_path (pathlib.Path): The absolute or relative path where the 
            config.ini file should be created. Must be a valid path object.
        silent (bool): If True, suppresses all console output during the 
            creation process. Defaults to False.

    Returns:
        None. Success is indicated by the successful creation of the file 
        at the specified location. Failure to write will raise an OSError.

    Side Effects and Thread-Safety:
        - Performs a synchronous write operation to the filesystem.
        - This function is not thread-safe if multiple threads attempt to write 
          to the same 'config_path' simultaneously.
    """
    config = configparser.ConfigParser()

    # Define the initial version for configuration tracking.
    config["Version"] = {"CURRENT_VERSION": "20251225"}

    # Debug settings are enabled by default in the builder to assist in early 
    # setup.
    config["Debug"] = {
        "ENABLE_DEBUG_MODE": "True",
        "ENABLE_DEBUG_SCREEN": "True",
        "SNMP_DEBUG_ENABLE": "True",
        "MIDI_DEBUG_ENABLE": "True",
        "OSC_DEBUG_ENABLE": "True",
        "AES70_DEBUG_ENABLE": "True",
    }

    # UI layout defaults use a 50/50 split for balanced visibility.
    config["UI"] = {
        "LAYOUT_SPLIT_EQUAL": "50",
        "LAYOUT_FULL_WEIGHT": "100",
        "RELOAD_CONFIG_DISPLAYED": "False",
    }

    # Default MQTT broker is set to localhost to encourage local-first 
    # connectivity.
    config["MQTT"] = {
        "BROKER_ADDRESS": "localhost",
        "BROKER_PORT": "1883",
        "MQTT_USERNAME": "guest",
        "MQTT_PASSWORD": "guest",
        "MQTT_RETAIN_BEHAVIOR": "True",
    }

    # Enable all scan agents by default to ensure maximum device discovery.
    config["ScanSettings"] = {
        "scan_gateways": "True",
        "scan_usb": "True",
        "scan_ip_direct": "True",
        "scan_aes70": "True",
        "scan_osc": "True",
        "scan_snmp": "True",
    }

    # OSC defaults use standard ports 8000/9000.
    config["OSC"] = {
        "osc_rx_port": "8000",
        "osc_tx_port": "9000",
        "osc_remote_ip": "127.0.0.1",
    }

    # Standard file write operation. Raises OSError if permissions are 
    # insufficient.
    with open(config_path, "w") as configfile:
        config.write(configfile)
