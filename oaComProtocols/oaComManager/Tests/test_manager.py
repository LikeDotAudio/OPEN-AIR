# oaComProtocols/oaComManager/Tests/test_manager.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Basic sanity test for ComProtocolManager.

import unittest
from oaComProtocols.oaComManager.Managers.manager import ComProtocolManager

class TestComProtocolManagerSanity(unittest.TestCase):
    def test_singleton_instance(self):
        """CHECK: Ensure ComProtocolManager is a singleton."""
        instance1 = ComProtocolManager.get_instance()
        instance2 = ComProtocolManager.get_instance()
        self.assertIs(instance1, instance2)

if __name__ == "__main__":
    unittest.main()
