# oaGui/Managers/lifecycle/ui_cache_invalidator.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Service for invalidating layout and image caches to force a fresh UI render.

def invalidate_ui_render_caches():
    """Clears global blueprint and image caches."""
    from oaGui.Core.factory.cache_image_store import CacheImageStore
    from oaGui.FileReaders.loader.json_blueprint_reader import JsonBlueprintReader
    
    JsonBlueprintReader.invalidate_cache()
    CacheImageStore.invalidate_cache()
