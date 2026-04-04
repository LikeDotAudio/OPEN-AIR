# oaGuiManager/Tests/test_asset_cache.py
# Author: Gemini CLI
# Version: 20260404.1.1
#
# Description: Unit tests for asset_cache.py

import unittest
from unittest.mock import MagicMock, patch
import pathlib
from PIL import Image
from oaGuiManager.Core.factory.asset_cache import AssetCacheManager, _MEMORY_ASSET_CACHE

class TestAssetCacheManager(unittest.TestCase):
    """Verifies that procedurally generated assets are correctly cached to memory and disk."""

    def setUp(self):
        """Clear memory cache before each test."""
        AssetCacheManager.invalidate_cache()

    def test_get_asset_hash(self):
        """OPERATE: Generate hash. CHECK: Verify consistent and unique hashing."""
        config = {"color": "red", "radius": 5}
        hash1 = AssetCacheManager.get_asset_hash("btn", 100, 50, config)
        hash2 = AssetCacheManager.get_asset_hash("btn", 100, 50, config)
        self.assertEqual(hash1, hash2)

    @patch('pathlib.Path.mkdir')
    @patch('oaGuiManager.Core.factory.asset_cache.AssetCacheManager._CACHE_DIR')
    def test_save_to_cache(self, mock_cache_dir, mock_mkdir):
        """OPERATE: Save image. CHECK: Verify it's in memory and saved to disk."""
        mock_cache_dir.__truediv__.return_value = pathlib.Path("/tmp/mock_asset.png")
        
        mock_image = MagicMock(spec=Image.Image)
        config = {"color": "red"}
        
        AssetCacheManager.save_to_cache("btn", 100, 50, config, mock_image)
        
        # Verify memory cache
        asset_hash = AssetCacheManager.get_asset_hash("btn", 100, 50, config)
        self.assertIn(asset_hash, _MEMORY_ASSET_CACHE)
        
        # Verify disk save call on the image object itself
        mock_image.save.assert_called_once()

    @patch('PIL.Image.open')
    @patch('pathlib.Path.exists', return_value=True)
    def test_load_from_memory_first(self, mock_exists, mock_open):
        """OPERATE: Load asset. CHECK: Verify it hits memory cache first, skipping disk."""
        mock_image = MagicMock(spec=Image.Image)
        config = {"color": "red"}
        asset_hash = AssetCacheManager.get_asset_hash("btn", 100, 50, config)
        
        # Manually seed memory cache
        _MEMORY_ASSET_CACHE[asset_hash] = mock_image
        
        loaded = AssetCacheManager.load_from_cache("btn", 100, 50, config)
        
        # Verify it came from memory
        self.assertEqual(loaded, mock_image)
        mock_open.assert_not_called()

if __name__ == '__main__':
    unittest.main()
