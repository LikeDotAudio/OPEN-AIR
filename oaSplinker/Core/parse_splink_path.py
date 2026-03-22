# Core/parse_splink_path.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

def parse_splink_path(self, path):
    """Splits 'topic:key' into (topic, key). Handles None."""
    if not path: return None, None
    if ":" in path:
        return path.split(":", 1)
    return path, None
