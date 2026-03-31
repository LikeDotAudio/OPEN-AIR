# 🏷️ Logging Matrix Manager

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
oaConfiguration/Managers/LoggingManager/manager.py

The **Logging Matrix Manager** is the central orchestrator for the 
hierarchical debugging system in OPEN-AIR. It transforms static 
logging into a dynamic, surgical tool that can be tuned at runtime. 
By using a tiered permission structure, it ensures that only the most 
relevant data reaches the logs, saving both CPU cycles and forensic 
analysis time.

## ⚙️ Assumptions & Constraints
- Assumes that `config.ini` contains a `[DEBUG_MATRIX]` section.
- Requires the `loguru` and `oaConfiguration.FileReaders.config_reader` 
  modules.
- The manager is a singleton and must be accessed via `get_instance()`.

## 📚 API Reference

### LoggingMatrixManager Class
#### `get_instance()`
Retrieves the thread-safe singleton instance of the manager.

**Returns:**
- `LoggingMatrixManager`: The global instance.

#### `is_debug_allowed(system, element, func_name)`
The primary gatekeeper for logging. Evaluates rules in this order:
1. **Master Killswitch**: If `MASTER_DEBUG_ENABLE` is False, all debug 
   logging is suppressed.
2. **Function Level**: Checks `MUTE_FUNCTIONS` and `FORCE_FUNCTIONS` 
   sets for high-precision control.
3. **Element Level**: Checks for `ELEMENT_<NAME>` flags in the matrix.
4. **System Level**: Checks for `SYS_<NAME>` flags (e.g., `SYS_CORE`).

**Parameters:**
- `system`: The subsystem name (e.g., 'CORE', 'MQTT').
- `element`: (Optional) Specific element within the system.
- `func_name`: (Optional) Name of the calling function.

**Returns:**
- `bool`: True if logging is permitted.

## 📝 Focus on Intent (Inline Comments)
- Singleton pattern ensures a single source of truth for debug states.
- Hierarchical evaluation allows for broad system toggles with 
  surgical function-level overrides.
- Robustness: Fallback defaults are provided if the configuration 
  system is not yet initialized.
- High-speed evaluation: Minimal overhead for gated log checks.
