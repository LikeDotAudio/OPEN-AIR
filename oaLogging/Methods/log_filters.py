# oaLogging/Methods/log_filters.py
# Author: Gemini (Collaborator)
# Version: 20260413.1000.1
#
# Description: Custom log filters for the OPEN-AIR logging system.

def rust_gate_filter(record):
    """
    ⚡ IRON OXIDE - PHASE 1: Universal Rust Gating
    Ensures every log call is gated by nanosecond-latency Rust checks.
    """
    if record["extra"].get("category") == "🚫 QUARANTINE":
        return False

    # Always allow high-gravity logs
    if record["level"].name in ["WARNING", "ERROR", "CRITICAL"]:
        return True

    # Extract clean partition and category names
    raw_part = record["extra"].get("partition", "")
    partition = raw_part.split()[-1].lower() if raw_part else "system"
    category = record["extra"].get("category", "").lower()
    func_name = record.get("function", "")

    from oaLogging.Methods.matrix_gate import is_debug_allowed
    return is_debug_allowed(partition, category, func_name)
