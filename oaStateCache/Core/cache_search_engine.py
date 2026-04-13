# Core/cache_search_engine.py
# Author: Anthony Peter Kuzub
# Version: 20260401.2300.1
#
# Description: High-performance Trie-based prefix mapping for state queries.
# Optimized with native Rust oatrie_rs for deterministic path lookups.

from typing import Any
from loguru import logger

# --- Native Rust Optimization ---
try:
    from oaRustCore import oa_trie_rs as oatrie_rs
    RUST_ENABLED = True
except ImportError:
    RUST_ENABLED = False
    logger.warning("⚠️ [STATE_CACHE] oatrie_rs not found. Falling back to slow Python prefix sets.")

class CacheSearchEngine:
    """Manages an optimized prefix tree for high-performance state queries."""

    def __init__(self):
        if RUST_ENABLED:
            self._trie = oatrie_rs.TopicTrie()
        else:
            self._active_prefixes = set()

    def rebuild(self, cache: dict):
        """Rebuilds the entire prefix structure from the provided cache."""
        if RUST_ENABLED:
            self._trie.clear()
            for topic in cache:
                self._trie.insert(topic)
        else:
            new_prefixes = set()
            for topic in cache:
                parts = topic.split('/')
                for i in range(1, len(parts)):
                    new_prefixes.add('/'.join(parts[:i]) + '/')
            self._active_prefixes = new_prefixes

    def add_topic(self, topic: str):
        """Incrementally adds a single new topic to the prefix structure."""
        if RUST_ENABLED:
            self._trie.insert(topic)
        else:
            parts = topic.split('/')
            for i in range(1, len(parts)):
                self._active_prefixes.add('/'.join(parts[:i]) + '/')

    def exists(self, prefix: str) -> bool:
        """Checks if any cached topics start with the given prefix."""
        if RUST_ENABLED:
            return self._trie.exists(prefix)
        else:
            if not prefix.endswith('/'): prefix += '/'
            return prefix in self._active_prefixes
