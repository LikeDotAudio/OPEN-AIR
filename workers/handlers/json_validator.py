# handlers/json_validator.py
#
# This module validates and sanitizes JSON data before it is published, ensuring it is serializable.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20250821.200641.1

import orjson
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args

current_version = "20251226.000000.1"


# Validates and sanitizes a dictionary to ensure it can be serialized into JSON.
# This function's primary role is to prevent `TypeError` during JSON serialization
# by checking if the provided data structure is compatible with `orjson.dumps()`.
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
        orjson.dumps(data)
        return data
    except TypeError as e:
        debug_logger(
            message=f"❌ JSON validation error: {e}. The data may not be fully serializable.",
            **_get_log_args(),
        )
        # For now, we will return the data as is and let the publisher handle the error.
        # A more advanced implementation could sanitize the data by removing non-serializable elements.
        return data