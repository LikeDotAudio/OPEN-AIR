# core/asset_cache_manager.py
#
# Utility to cache procedurally generated assets (panels, screws, etc) to disk and memory.
# Prevents expensive PIL re-generation and redundant disk I/O.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20260218.Optimization.1

import os
import hashlib
import orjson
from pathlib import Path
from PIL import Image

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.config_reader import Config
from oaOchestration.project_paths import GLOBAL_PROJECT_ROOT

app_constants = Config.get_instance()

# ⚡ OPTIMIZATION: Process-lifetime memory cache for loaded assets.
# This prevents millions of __del__ calls and Tkinter window management spam.
_MEMORY_ASSET_CACHE = {}

class AssetCacheManager:
    """Manages disk and memory caching for procedurally generated PIL images."""
    
    # ⚡ OPTIMIZATION: Use absolute path relative to project root
    from oaOchestration.path_initializer import DATA_CACHE_DIR
    _CACHE_DIR = DATA_CACHE_DIR / "assets"
    
    @classmethod
    def _ensure_cache_dir(cls):
        """Ensures the cache directory exists."""
        if not cls._CACHE_DIR.exists():
            cls._CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def invalidate_cache(cls):
        """Clears the in-memory asset cache."""
        global _MEMORY_ASSET_CACHE
        _MEMORY_ASSET_CACHE.clear()
        if LOCAL_DEBUG: logger.info("♻️ AssetCacheManager: Memory cache cleared.")

    @classmethod
    def get_asset_hash(cls, key_prefix, width, height, config):
        """Generates a unique hash for a specific asset configuration."""
        # Convert config to a stable JSON string for hashing
        config_json = orjson.dumps(config, option=orjson.OPT_SORT_KEYS)
        hash_input = f"{key_prefix}_{width}x{height}_{config_json.decode()}"
        # Using SHA256 for better collision resistance and to satisfy security audits.
        return hashlib.sha256(hash_input.encode()).hexdigest()

    @classmethod
    def load_from_cache(cls, key_prefix, width, height, config):
        """Loads an image from memory or disk if it exists and is healthy."""
        asset_hash = cls.get_asset_hash(key_prefix, width, height, config)
        
        # 1. Check Memory Cache First (FASTEST)
        if asset_hash in _MEMORY_ASSET_CACHE:
            return _MEMORY_ASSET_CACHE[asset_hash]

        # 2. Check Disk Cache
        cls._ensure_cache_dir()
        cache_path = cls._CACHE_DIR / f"{asset_hash}.png"
        
        if cache_path.exists():
            try:
                img = Image.open(cache_path)
                # ⚡ MANDATORY INTEGRITY CHECK: 
                # Force PIL to actually read the pixel data. 
                img.load() 
                
                # Cache in memory for next time
                _MEMORY_ASSET_CACHE[asset_hash] = img
                return img
            except Exception as e:
                # If the image is corrupted (truncated, empty, etc), delete it!
                if LOCAL_DEBUG:
                    logger.exception("❌ Corrupted cache file detected and removed: {} ({})", cache_path.name, str(e))
                try:
                    os.remove(cache_path)
                except:
                    pass
        return None

    @classmethod
    def save_to_cache(cls, key_prefix, width, height, config, pil_image):
        """Saves a generated image to the disk and memory cache."""
        asset_hash = cls.get_asset_hash(key_prefix, width, height, config)
        
        # Save to memory cache immediately
        _MEMORY_ASSET_CACHE[asset_hash] = pil_image

        # Save to disk cache asynchronously (or immediately for now)
        cls._ensure_cache_dir()
        cache_path = cls._CACHE_DIR / f"{asset_hash}.png"
        
        try:
            pil_image.save(cache_path, "PNG")
        except Exception as e:
            logger.exception("❌ Error saving asset cache")
