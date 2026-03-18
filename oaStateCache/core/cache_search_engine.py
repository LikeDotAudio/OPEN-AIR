from typing import Set

class CacheSearchEngine:
    """Manages an O(1) prefix map for high-performance state queries."""

    def __init__(self):
        self.active_prefixes: Set[str] = set()

    def rebuild(self, cache):
        """Rebuilds the entire prefix set from the provided cache dictionary."""
        new_prefixes = set()
        for topic in cache:
            parts = topic.split('/')
            for i in range(1, len(parts)):
                new_prefixes.add('/'.join(parts[:i]) + '/')
        self.active_prefixes = new_prefixes

    def add_topic(self, topic: str):
        """Incrementally adds prefixes for a single new topic."""
        parts = topic.split('/')
        for i in range(1, len(parts)):
            self.active_prefixes.add('/'.join(parts[:i]) + '/')

    def exists(self, prefix: str) -> bool:
        """Checks if any cached topics start with the given prefix."""
        if not prefix.endswith('/'): prefix += '/'
        return prefix in self.active_prefixes
