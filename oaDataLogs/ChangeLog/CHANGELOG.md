## [2026-04-11 01:45:00] - Fix SNMP Status & WYSIWYG Logging
**************************************
Commit: 0aba269ad8cee1c541e165020b9c8a4179301479
Date: 2026-04-11 01:58:01 -0400
Message: Fix SNMP Status & WYSIWYG Logging
**************************************

- **Fix (SNMP):** Disabled the redundant `SNMPObserver` instance that was running in the UI partition. This was causing conflicting status messages to be published to the `OPEN-AIR/System/Status/SNMP/Bridge` topic, resulting in the UI displaying a blank or incorrect status. With this change, only the `SNMPBridge` in the CORE partition manages and reports SNMP status, ensuring accurate display.
- **Fix (WYSIWYG):** Corrected an `AttributeError` in the `run_builder.py` script. The script was attempting to call a non-existent `get_log_directory()` method. The code has been updated to use the standard `initialize_paths()` and `set_log_directory()` functions to correctly configure the logging service for the WYSIWYG editor partition.
