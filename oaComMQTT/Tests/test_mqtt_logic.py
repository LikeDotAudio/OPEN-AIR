# Tests/test_mqtt_logic.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import unittest
from unittest.mock import MagicMock, patch
from oaTranslator.Core.topic_calculator import TopicCalculator
# Using a robust path to import from the moved Workers location for MQTTSweeper
import sys
import os
# Calculate the project root by going up three levels from the current file
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from oaTests.Workers.CleanupApps.ClearMQTT import MQTTSweeper

class TestMQTTLogic(unittest.TestCase):
    def test_topic_calculator_calculate(self):
        """Validate string manipulation for dynamic MQTT topics based on UI hierarchy."""
        calc = TopicCalculator(base_topic="OPEN-AIR")
        
        # Test basic formatting
        topic = calc.calculate("volume", "MainTab")
        self.assertEqual(topic, "OPEN-AIR/MainTab/volume")
        
        # Test stripping layout/structural tokens
        topic_with_extra = calc.calculate("gui/knob1", "oaGuiDefinitions/Tab1")
        self.assertNotIn("display", topic_with_extra)
        self.assertNotIn("gui", topic_with_extra)
        self.assertEqual(topic_with_extra, "OPEN-AIR/Tab1/knob1")

    def test_mqtt_sweeper_on_message_filter(self):
        """Verify on_message correctly filters for the configured base topic."""
        sweeper = MQTTSweeper("localhost", 1883, "OPEN-AIR")
        
        # Mock message objects
        msg_in_root = MagicMock()
        msg_in_root.topic = "OPEN-AIR/some/topic"
        
        msg_outside = MagicMock()
        msg_outside.topic = "OTHER-PROJECT/topic"
        
        # Trigger on_message
        sweeper.on_message(None, None, msg_in_root)
        sweeper.on_message(None, None, msg_outside)
        
        # Check results
        self.assertIn("OPEN-AIR/some/topic", sweeper.topics)
        self.assertNotIn("OTHER-PROJECT/topic", sweeper.topics)

if __name__ == "__main__":
    unittest.main()
