# Interface/Tabs/ElementProperties/Methods/path_resolver.py
# Author: Anthony Peter Kuzub
# Version: 20260417.001.0
#
# Description: Standardizes path strings for internal resolution.

def normalize_path(path, state_manager):
    """Standardizes path strings for internal resolution."""
    if not path: return ""
    normalized = str(path).strip().strip('.')
    if normalized.lower() == "root": return ""
    
    # If path is already valid, return as is
    if state_manager.get_value_at_path(normalized) is not None:
        return normalized

    full_state = state_manager.get_state()
    if full_state:
        root_keys = list(full_state.keys())
        # If it's a relative path, try to find which root it belongs to
        for root in root_keys:
            candidate = f"{root}.{normalized}"
            if state_manager.get_value_at_path(candidate) is not None:
                return candidate
    return normalized
