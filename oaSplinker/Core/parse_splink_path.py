def parse_splink_path(self, path):
    """Splits 'topic:key' into (topic, key). Handles None."""
    if not path: return None, None
    if ":" in path:
        return path.split(":", 1)
    return path, None
