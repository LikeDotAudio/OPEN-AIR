# workers/handlers/json_validator.py
#
# Purpose: Ensures the JSON being published is valid before it leaves the airlock.
# Key Function: validate_and_sanitize_json(data: dict) -> dict

import orjson
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args

current_version = "20251226.000000.1"


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
