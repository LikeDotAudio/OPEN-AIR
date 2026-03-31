# Methods/json_validator.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: This module validates and sanitizes JSON data before it is published, ensuring it is serializable.

import orjson

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()

current_version = "20251226.000000.1"


# Validates and sanitizes a dictionary to ensure it can be serialized into JSON.
# This function's primary role is to prevent `TypeError` during JSON serialization
# by checking if the provided data structure is compatible with `orjson.dumps().decode()`.
# Inputs:
#     data (dict): The dictionary to be validated and sanitized.
# Outputs:
#     dict: The original data dictionary if valid, or a potentially modified one if sanitization is added.
def validate_and_sanitize_json(data: dict) -> dict:
    """
    Ensures the data is a valid JSON structure before publishing.
    For now, it just ensures it can be dumped to JSON.
    Sanitization logic can be added later if needed.
    """
    try:
        # The main purpose is to ensure that the data can be serialized to JSON.
        orjson.dumps(data).decode()
        return data
    except TypeError as e:
        logger.error(f"❌ JSON validation error: {e}. The data may not be fully serializable.")
        # For now, we will return the data as is and let the publisher handle the error.
        # A more advanced implementation could sanitize the data by removing non-serializable elements.
        return data
