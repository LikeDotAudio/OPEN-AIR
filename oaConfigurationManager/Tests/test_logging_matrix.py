# oaConfigurationManager/Tests/test_logging_matrix.py
# Author: Gemini QA Lead
# Version: 20260330.0001.1
#
# Description: Unit tests for the Hierarchical Debug Matrix logic.

import unittest

from oaConfigurationManager.Managers.LoggingManager.manager import LoggingMatrixManager


class TestLoggingMatrixManager(unittest.TestCase):
    def setUp(self):
        """Build: Initialize manager with a clean slate."""
        # Reset singleton for testing
        LoggingMatrixManager._instance = None
        self.manager = LoggingMatrixManager.get_instance()

        # Inject a known test matrix
        self.test_matrix = {
            "MASTER_DEBUG_ENABLE": True,
            "SYS_COMMS": False,
            "SYS_GUI": True,
            "ELEMENT_MQTT": True, # Override COMMS
            "ELEMENT_SNMP": False # Follow COMMS (redundant but explicit)
        }
        self.manager._matrix = self.test_matrix
        self.manager._mute_functions = {"noisy_loop", "heart_beat"}
        self.manager._force_functions = {"critical_init"}

    def test_master_killswitch(self):
        """Check: Master False overrides everything."""
        self.manager._matrix["MASTER_DEBUG_ENABLE"] = False
        # Even if GUI is True, Master False should win
        self.assertFalse(self.manager.is_debug_allowed("GUI"))
        # Even if function is forced, Master False should win
        self.assertFalse(self.manager.is_debug_allowed("GUI", func_name="critical_init"))

    def test_system_level_gating(self):
        """Check: System flags are respected."""
        self.assertTrue(self.manager.is_debug_allowed("GUI"))
        self.assertFalse(self.manager.is_debug_allowed("DATA")) # Default False

    def test_element_override(self):
        """Check: Element overrides parent system state."""
        # Comms is False, but MQTT is explicitly True
        self.assertTrue(self.manager.is_debug_allowed("COMMS", element="MQTT"))
        # Comms is False, and SNMP is False
        self.assertFalse(self.manager.is_debug_allowed("COMMS", element="SNMP"))

    def test_function_level_precision(self):
        """Check: Function inclusions/exclusions have highest priority."""
        # GUI is True, but noisy_loop is muted
        self.assertFalse(self.manager.is_debug_allowed("GUI", func_name="noisy_loop"))

        # COMMS is False, but critical_init is forced
        self.assertTrue(self.manager.is_debug_allowed("COMMS", func_name="critical_init"))

    def test_hot_update(self):
        """Operate: Update matrix at runtime."""
        self.manager.update_matrix("SYS_DATA", True)
        self.assertTrue(self.manager.is_debug_allowed("DATA"))

if __name__ == "__main__":
    unittest.main()
