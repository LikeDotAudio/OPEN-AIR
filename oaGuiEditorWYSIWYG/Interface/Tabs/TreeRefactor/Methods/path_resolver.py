# Interface/Tabs/TreeRefactor/Methods/path_resolver.py
# Author: Gemini CLI
# Version: 20260417.001.0
#
# Description: Standardizes path strings for internal resolution.

def normalize_path(path, state_manager):
    """Standardizes path strings for internal resolution."""
    if not path: return ""
    normalized = str(path).strip().strip('.')
    if normalized.lower() == "root": return ""

    full_state = state_manager.get_state()
    if full_state:
        root_keys = list(full_state.keys())
        if len(root_keys) == 1:
            root_name = root_keys[0]
            if not normalized.startswith(root_name) and not normalized.startswith(f"{root_name}."):
                candidate = f"{root_name}.{normalized}"
                if state_manager.get_value_at_path(candidate) is not None:
                    normalized = candidate
    return normalized
