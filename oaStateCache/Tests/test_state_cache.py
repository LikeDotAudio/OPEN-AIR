# Tests/test_state_cache.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import unittest
from unittest.mock import MagicMock, patch
from oaStateCache.Core.state_cache import StateRegistry

class TestStateCache(unittest.TestCase):
    def setUp(self):
        self.mqtt = MagicMock()
        with patch("oaStateCache.Core.state_cache.cache_io_handler.load_cache", return_value={}):
            self.registry = StateRegistry(self.mqtt)

    def test_handle_external_update(self):
        """Goal: Verify that external updates are correctly cached, persisted, and broadcast."""
        # Mock dependencies
        self.registry.save_engine = MagicMock()
        self.registry.observers = MagicMock()
        
        with patch("oaComBroker.Managers.protocol_router.ProtocolRouter.get_instance") as mock_router_get:
            mock_router = mock_router_get.return_value
            with patch("oaTranslator.Core.manifest.builder.create_manifest", return_value={"val": 42}):
                
                self.registry.handle_external_update("TEST/TOPIC", 42, source="GUI")
                
                # CHECK: Cached
                self.assertEqual(self.registry.cache["TEST/TOPIC"]["val"], 42)
                # CHECK: Persisted
                self.registry.save_engine.schedule_save.assert_called()
                # CHECK: Observers notified
                self.registry.observers.notify.assert_called_with("TEST/TOPIC", {"val": 42})
                # CHECK: ProtocolRouter Ingested (which leads to MQTT Published)
                mock_router.ingest.assert_called()

if __name__ == "__main__":
    unittest.main()
