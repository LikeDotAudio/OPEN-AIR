# oaTests/Managers/configIniEditor/manager.py
# Author: Anthony Peter Kuzub
# Version: 20260329.2359.1
#
# Description: Specialized manager for editing config.ini directly from the TUI.
# Focuses on the [DEBUG_MATRIX] section for hierarchical logging control.

import configparser
import pathlib
from loguru import logger

class ConfigIniEditor:
    """
    Manages direct read/write operations on config.ini.
    Provides a clean API for the Textual UI to toggle debug flags.
    """

    def __init__(self, config_path=None):
        if config_path is None:
            from oaOchestration.Core.path_initializer import GLOBAL_PROJECT_ROOT
            config_path = GLOBAL_PROJECT_ROOT / "config.ini"
        
        self.config_path = pathlib.Path(config_path)
        self.config = configparser.ConfigParser()
        self._ensure_config_exists()

    def _ensure_config_exists(self):
        """Re-reads the config file to ensure we have the latest state."""
        if self.config_path.exists():
            self.config.read(self.config_path)
        else:
            logger.error(f"❌ ConfigIniEditor: config.ini not found at {self.config_path}")

    def get_debug_matrix_flags(self):
        """
        Returns a dictionary of all boolean flags in the [DEBUG_MATRIX] section.
        """
        self._ensure_config_exists()
        flags = {}
        if "DEBUG_MATRIX" in self.config:
            section = self.config["DEBUG_MATRIX"]
            for key in section:
                # Skip the list-based keys
                if key.lower() in ["mute_functions", "force_functions"]:
                    continue
                try:
                    flags[key] = self.config.getboolean("DEBUG_MATRIX", key)
                except ValueError:
                    pass
        return flags

    def set_debug_flag(self, key, value):
        """
        Updates a specific flag in the [DEBUG_MATRIX] and writes to disk.
        """
        self._ensure_config_exists()
        if "DEBUG_MATRIX" not in self.config:
            self.config["DEBUG_MATRIX"] = {}
        
        # Convert bool to string for INI
        self.config["DEBUG_MATRIX"][key] = str(value)
        
        try:
            with open(self.config_path, 'w') as configfile:
                self.config.write(configfile)
            logger.success(f"💾 [CONFIG] Updated {key} to {value} in {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to write config.ini: {e}")
            return False

    def get_all_debug_sections(self):
        """Returns the full hierarchical debug setup for UI generation."""
        self._ensure_config_exists()
        # Return structured data for the UI
        return {
            "master": self.config.getboolean("DEBUG_MATRIX", "master_debug_enable", fallback=False),
            "systems": {
                "COMMS": self.config.getboolean("DEBUG_MATRIX", "sys_comms", fallback=False),
                "GUI": self.config.getboolean("DEBUG_MATRIX", "sys_gui", fallback=False),
                "DATA": self.config.getboolean("DEBUG_MATRIX", "sys_data", fallback=False),
                "ROUTER": self.config.getboolean("DEBUG_MATRIX", "sys_router", fallback=False),
                "CORE": self.config.getboolean("DEBUG_MATRIX", "sys_core", fallback=False),
            },
            "elements": {
                "MQTT": self.config.getboolean("DEBUG_MATRIX", "element_mqtt", fallback=False),
                "SNMP": self.config.getboolean("DEBUG_MATRIX", "element_snmp", fallback=False),
                "MIDI": self.config.getboolean("DEBUG_MATRIX", "element_midi", fallback=False),
                "OSC": self.config.getboolean("DEBUG_MATRIX", "element_osc", fallback=False),
                "BUILDER": self.config.getboolean("DEBUG_MATRIX", "element_gui_builder", fallback=False),
            }
        }
