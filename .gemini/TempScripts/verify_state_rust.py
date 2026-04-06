
import sys
import os

project_root = "/home/anthony/Documents/OPEN-AIR"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Mock loggers to prevent noise
import logging
logging.basicConfig(level=logging.CRITICAL)

try:
    from oaStateCache.Core.state_cache import HAS_RUST as STATEREG_RUST
    from oaStateCache.Core.cache_search_engine import RUST_ENABLED as TRIE_RUST

    print(f"✅ StateRegistry Core HAS_RUST: {STATEREG_RUST}")
    print(f"✅ CacheSearchEngine RUST_ENABLED: {TRIE_RUST}")
except Exception as e:
    print(f"❌ Error verifying StateCache Rust modules: {e}")
