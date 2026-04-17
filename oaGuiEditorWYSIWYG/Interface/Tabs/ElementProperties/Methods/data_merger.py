# Interface/Tabs/ElementProperties/Methods/data_merger.py
# Author: Anthony Peter Kuzub
# Version: 20260417.001.0
#
# Description: Recursive dictionary merging utility.

def deep_merge(template, actual):
    """Recursively merges actual data into a template dictionary."""
    if not isinstance(template, dict) or not isinstance(actual, dict):
        return actual
    result = template.copy()
    for k, v in actual.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result
