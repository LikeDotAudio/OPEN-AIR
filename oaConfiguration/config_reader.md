# 🏷️ Config Reader

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
managers/configini/config_reader.py

This module defines the 'Config' class, which acts as a centralized, thread-safe singleton for managing application-wide settings. It handles reading from 'config.ini', environment variable overrides, and provides a unified interface for accessing configuration parameters.

Author: Anthony Peter Kuzub

## ⚙️ Assumptions & Constraints
- Assumes a singleton pattern to ensure consistency across the application.
- Requires thread-safe initialization using locks.
- Depends on 'configparser' for INI parsing and 'pathlib' for path management.
- Expects certain environment variables (e.g., OPEN_AIR_INSTANCE_GUID) for supervisor-led deployments.

## 📚 API Reference

### Classes
#### `class Config`
Manages application configuration settings as a thread-safe singleton.

##### `__init__(self)`
Initializes the Config object upon its first instantiation.

**Parameters:**
- None

**Returns:**
- None. Internal state is updated by calling 'read_config()'.

**Side Effects & Thread-Safety:**
- Triggers filesystem I/O through 'read_config()'.
- Sets '_initialized' flag to prevent multiple initializations.
- This method is intended to be called only via 'get_instance()'.

##### `get_instance(cls)`
Provides access to the singleton Config instance.

**Parameters:**
- None

**Returns:**
- Config: The existing singleton instance, or a newly created one if none exists.

**Side Effects & Thread-Safety:**
- Uses a class-level lock to ensure thread-safety during initialization.
- Guarantees that only one instance of Config exists in the process.

##### `global_settings(self)`
Retrieves a dictionary of global debug and logging settings.

**Parameters:**
- None

**Returns:**
- dict: A dictionary containing Boolean flags for various debug states.

**Side Effects & Thread-Safety:**
- Caches the generated dictionary in '_cached_global_settings' to minimize overhead.
- This property is thread-safe for reading after initial caching.

##### `get_mqtt_base_topic(self)`
Retrieves the configured base MQTT topic.

**Parameters:**
- None

**Returns:**
- str: The base topic string (e.g., 'OPEN-AIR').

**Side Effects & Thread-Safety:**
- Thread-safe for read-only access.

##### `read_config(self)`
Parses 'config.ini' and updates instance attributes accordingly.

**Parameters:**
- None

**Returns:**
- None. Attributes of the instance are updated in-place.

**Side Effects & Thread-Safety:**
- Performs filesystem I/O (read/write).
- May execute an external 'Setup.py' subprocess if config is missing.
- Updates global instance state; should be called during initialization.

## 📝 Focus on Intent (Inline Comments)
- Ensures atomic initialization in multi-threaded environments.
- Default values serve as fallbacks if settings are missing from config.ini.
- Instance identity is crucial for distinguishing messages in a multi-node MQTT network.
- Recreate config if it disappeared to prevent system stall.
- Setup script ensures that all OS-level dependencies are satisfied after a fresh config generation.
- Environment variables allow the supervisor to keep session identity across partition restarts without writing to disk.
- PID ensures that logs and temporary files from different instances do not collide.
