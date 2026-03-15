# GUI File Loader

This module (`gui_file_loader.py`) handles **File I/O** for the GUI builder. It reads the JSON configuration file, verifies content integrity (hashing), and parses the JSON.

## Features
- **Hash Verification**: Prevents unnecessary rebuilds if the file content hasn't changed.
- **Safe Parsing**: Uses `orjson` for fast and safe JSON loading.
- **Initialization**: Publishes the loaded config to MQTT for system awareness.

## Usage
Internal mixin for `DynamicGuiBuilder`.