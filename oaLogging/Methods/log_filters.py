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
    if record["extra"].get("category_name") == "QUARANTINE":
        return False

    # Always allow high-gravity logs
    if record["level"].name in ["WARNING", "ERROR", "CRITICAL"]:
        return True

    # Extract clean partition and category names
    raw_part = record["extra"].get("partition", "")
    partition = raw_part.split()[-1].lower() if raw_part else "system"
    category = record["extra"].get("category_name", "SYSTEM").lower()
    func_name = record.get("function", "")

    # ⚡ MAPPING: Normalize generic 'comms' logs to use the category as element
    # This allows 'element_smpte2138' to gate both matrix_log and direct logger calls.
    sys_lookup = partition
    el_lookup = category
    
    if partition == "system" and category != "system":
        # If it's a protocol log but partition isn't set, try 'comms' as fallback system
        from oaLogging.Methods.matrix_gate import is_debug_allowed
        if not is_debug_allowed("comms", category, func_name):
            return False

    from oaLogging.Methods.matrix_gate import is_debug_allowed
    return is_debug_allowed(sys_lookup, el_lookup, func_name)
