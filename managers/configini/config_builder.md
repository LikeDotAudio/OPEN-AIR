# 🏷️ Config Builder

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
managers/configini/config_builder.py

This module provides a mechanism to generate a default 'config.ini' file containing the necessary settings for the OPEN-AIR system to function. It ensures that even in the absence of a pre-existing configuration, the system has sensible defaults to fall back on.

## ⚙️ Assumptions & Constraints
- Assumes the caller has write permissions to the destination directory.
- Requires the 'configparser' and 'pathlib' modules.
- The generated file follows the standard INI format.

## 📚 API Reference

### Global Functions
#### `create_default_config_ini(config_path, silent)`
Creates a default config.ini file with predefined settings.

**Parameters:**
- `config_path`: The absolute or relative path where the config.ini file should be created. Must be a valid path object.
- `silent`: If True, suppresses all console output during the creation process. Defaults to False.

**Returns:**
- None. Success is indicated by the successful creation of the file at the specified location. Failure to write will raise an OSError.

**Side Effects & Thread-Safety:**
- Performs a synchronous write operation to the filesystem.
- This function is not thread-safe if multiple threads attempt to write to the same 'config_path' simultaneously.

## 📝 Focus on Intent (Inline Comments)
- Define the initial version for configuration tracking.
- Debug settings are enabled by default in the builder to assist in early setup.
- UI layout defaults use a 50/50 split for balanced visibility.
- Default MQTT broker is set to localhost to encourage local-first connectivity.
- Enable all scan agents by default to ensure maximum device discovery.
- OSC defaults use standard ports 8000/9000.
- Standard file write operation. Raises OSError if permissions are insufficient.
