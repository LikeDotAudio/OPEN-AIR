# utils/test_utils.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import json
from pathlib import Path


def load_sample_config(component_path, entry_key=None):
    """
    Loads a sample.json from the specified component path or its Assets/ subdirectory.
    If entry_key is provided, returns that specific entry.
    Otherwise returns the first non-README entry found.
    """
    sample_file = Path(component_path) / 'sample.json'
    if not sample_file.exists():
        # Standard: Also check Assets/
        sample_file = Path(component_path) / 'Assets' / 'sample.json'

    if not sample_file.exists():
        raise FileNotFoundError(f'Sample file not found: {sample_file}')
    with open(sample_file) as f:
        data = json.load(f)
    if entry_key and entry_key in data:
        return data[entry_key]
    for k, v in data.items():
        if not k.startswith('_'):
            return v
    return data
