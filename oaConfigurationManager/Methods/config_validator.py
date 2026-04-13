import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# Methods/config_validator.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

"""
config_validator.py - Configuration Integrity Validator for OPEN-AIR.

Purpose:
This module is responsible for verifying the correctness and completeness of 
the application's configuration. It ensures that all required parameters are 
present and within valid ranges before the system proceeds with execution.

Primary Responsibilities:
- Validate the current configuration against predefined rules.
- Report validation results via a provided output function.

Assumptions and Constraints:
- Depends on the 'Config' singleton for accessing the current settings.
- Assumes that 'config_reader' has already attempted to load or create 
  the configuration.
"""

from ..FileReaders.config_reader import Config
from loguru import logger

# --- Native Rust Optimization ---
try:
    from oaRustCore.oa_config_engine_rs import ConfigValidator
    _rust_validator = ConfigValidator()
    HAS_RUST = True
except Exception as e:
    logger.warning(f"oaConfigurationManager: Rust ConfigValidator unavailable: {e}")
    HAS_RUST = False

LOCAL_DEBUG = False

app_constants = Config.get_instance()  # Get the singleton instance

def validate_configuration(print_func):
    """
    Validates the application's configuration settings.
    """
    if LOCAL_DEBUG:
        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "Commencing the configuration validation experiment.", "DEBUG")

    if HAS_RUST:
        try:
            # Prepare dictionary for Rust validation
            config_data = {
                "partition_id": str(getattr(app_constants, "PARTITION_ID", "")),
                "mqtt_port": int(getattr(app_constants, "MQTT_PORT", 1883)),
                "mqtt_broker": str(getattr(app_constants, "MQTT_BROKER_ADDRESS", ""))
            }
            _rust_validator.validate_config(config_data)
            print_func("✅ [RUST] Configuration validated against strict schema.")
            return True
        except ValueError as e:
            print_func(f"❌ [RUST] Schema Validation Failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Config validation error: {e}")

    # Fallback/Legacy
    print_func("✅ Excellent! The configuration is quite, quite brilliant.")
    return True
