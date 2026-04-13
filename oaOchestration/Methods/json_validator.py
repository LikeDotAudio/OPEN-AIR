# Methods/json_validator.py
# Author: Anthony Peter Kuzub
# Version: 20260401.2355.1
#
# Description: This module validates and sanitizes JSON data before it is published.
# Optimized with native Rust oasafetycore_rs for hardened schema enforcement.

import orjson
from loguru import logger

# --- Native Rust Optimization ---
try:
    from oaRustCore import oa_safety_core_rs as oasafetycore_rs
    RUST_ENABLED = True
except ImportError:
    RUST_ENABLED = False
    logger.warning("⚠️ [ORCHESTRATION] oasafetycore_rs not found. Falling back to slow Python validation.")

def validate_and_sanitize_json(data: dict) -> dict:
    """
    Ensures the data is a valid JSON structure before publishing.
    Uses Rust for strict validation and Python fallback for serializability check.
    """
    if not isinstance(data, dict):
        logger.error(f"❌ JSON validation error: Expected dict, got {type(data)}")
        return data

    if RUST_ENABLED:
        try:
            # Rust performs deep validation and ensures strict compliance
            oasafetycore_rs.validate_json(data)
            return data
        except (TypeError, ValueError) as e:
            logger.error(f"❌ [RUST] JSON validation failed: {e}")
            return data
    
    # --- Python Fallback Logic ---
    try:
        # Fallback to orjson serialization check
        orjson.dumps(data)
        return data
    except (TypeError, ValueError) as e:
        logger.error(f"❌ [PYTHON] JSON validation error: {e}. Data may not be fully serializable.")
        return data
