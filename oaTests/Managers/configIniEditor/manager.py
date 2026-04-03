import pathlib

import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# oaTests/Managers/configIniEditor/manager.py
# Author: Anthony Peter Kuzub
# Version: 20260330.0030.1
#
# Description: Specialized manager for editing config.ini directly from the TUI.
# Handles multiple sections while preserving comments and formatting.

import configparser
from loguru import logger

class ConfigIniEditor:
    """
    Manages direct read/write operations on config.ini.
    Provides a clean API for the Textual UI to toggle configuration flags.
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

    def get_section_flags(self, section_name):
        """
        Returns a dictionary of all boolean flags in a specific section.
        """
        self._ensure_config_exists()
        flags = {}
        if section_name in self.config:
            section = self.config[section_name]
            for key in section:
                # Skip the list-based keys in DEBUG_MATRIX
                if section_name == "DEBUG_MATRIX" and key.lower() in ["mute_functions", "force_functions"]:
                    continue
                try:
                    flags[key] = self.config.getboolean(section_name, key)
                except ValueError:
                    pass
        return flags

    def set_config_flag(self, section, key, value):
        """
        Surgically updates a specific flag in any section while preserving comments.
        """
        try:
            with open(self.config_path, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            logger.error(f"❌ Failed to read config.ini: {e}")
            return False

        new_lines = []
        current_section = None
        key_found = False
        val_str = "True" if value is True else "False" if value is False else str(value)

        for line in lines:
            stripped = line.strip()
            
            # Identify section
            if stripped.startswith('[') and stripped.endswith(']'):
                current_section = stripped[1:-1].strip()
                new_lines.append(line)
                continue
            
            # If in the correct section, look for the key
            if current_section == section and not stripped.startswith('#') and '=' in stripped:
                line_key, line_val = stripped.split('=', 1)
                if line_key.strip().lower() == key.lower():
                    # Preserve existing indentation and comments on the same line
                    indent = line[:line.find(line_key)]
                    comment = ""
                    if '#' in line_val:
                        comment = " #" + line_val.split('#', 1)[1].rstrip()
                    
                    new_lines.append(f"{indent}{line_key.strip()} = {val_str}{comment}\n")
                    key_found = True
                    continue
            
            new_lines.append(line)

        # If the key didn't exist in the section, add it at the end of the section
        if not key_found:
            insert_pos = -1
            found_section = False
            for i, line in enumerate(new_lines):
                if line.strip() == f"[{section}]":
                    found_section = True
                    continue
                if found_section and line.strip().startswith('['):
                    insert_pos = i
                    break
            
            if insert_pos == -1: # End of file or section was the last one
                new_lines.append(f"{key} = {val_str}\n")
            else:
                new_lines.insert(insert_pos, f"{key} = {val_str}\n")

        try:
            with open(self.config_path, 'w') as f:
                f.writelines(new_lines)
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💾 [CONFIG] Surgically updated [{section}] {key} to {value}", "SUCCESS")
            
            # Sync the internal configparser for immediate read consistency
            self.config.read(self.config_path)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to write config.ini: {e}")
            return False

    # --- Legacy Compatibility ---
    def get_debug_matrix_flags(self):
        return self.get_section_flags("DEBUG_MATRIX")

    def set_debug_flag(self, key, value):
        return self.set_config_flag("DEBUG_MATRIX", key, value)

    def get_all_debug_sections(self):
        """Returns the full hierarchical debug setup for UI generation."""
        self._ensure_config_exists()
        return {
            "master": self.config.getboolean("DEBUG_MATRIX", "master_debug_enable", fallback=False),
            "debug": self.get_section_flags("Debug"),
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
                "AES70": self.config.getboolean("DEBUG_MATRIX", "element_aes70", fallback=False),
                "REST": self.config.getboolean("DEBUG_MATRIX", "element_rest", fallback=False),
                "BUILDER": self.config.getboolean("DEBUG_MATRIX", "element_gui_builder", fallback=False),
            }
        }