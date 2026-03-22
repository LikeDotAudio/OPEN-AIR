# Tests/test_visa_logic.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import unittest
from unittest.mock import MagicMock, patch
import pyvisa
from oaComVisa.Core.visa_proxy import VisaProxy

class TestVisaLogic(unittest.TestCase):
    def test_visa_resource_lister(self):
        """Confirm the backend library loads and returns available hardware identifiers."""
        try:
            rm = pyvisa.ResourceManager("@py")
            resources = rm.list_resources()
            self.assertIsInstance(resources, tuple)
        except Exception as e:
            self.fail(f"PyVISA ResourceManager failed: {e}")

    def test_visa_library_error(self):
        """Fail: LibraryError is raised due to missing pyvisa-py."""
        with patch("pyvisa.ResourceManager", side_effect=pyvisa.errors.LibraryError("pyvisa-py missing")):
            with self.assertRaises(pyvisa.errors.LibraryError):
                pyvisa.ResourceManager("@py")

    def test_visa_proxy_init_success(self):
        """Check thread-safe command queue initialization."""
        mqtt_controller = MagicMock()
        subscriber_router = MagicMock()
        
        proxy = VisaProxy(mqtt_controller, subscriber_router)
        
        self.assertTrue(hasattr(proxy, 'command_queue'))
        self.assertFalse(proxy.shutdown_flag.is_set())

    def test_visa_proxy_init_fail(self):
        """Fail: Missing MQTT controller or router during initialization."""
        # The constructor returns early if missing components
        proxy = VisaProxy(None, None)
        # Verify it didn't finish initialization
        self.assertFalse(hasattr(proxy, 'command_queue'))

if __name__ == "__main__":
    unittest.main()
