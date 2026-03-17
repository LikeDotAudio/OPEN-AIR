import unittest
from unittest.mock import MagicMock, patch
from workers.logic.core.topic_calculator import TopicCalculator
# Using sys.path to import from a non-standard location for MQTTSweeper
import sys
import os
sys.path.append(os.path.abspath("assets/Testing/FlameGraph/core"))
from ClearMQTT import MQTTSweeper

class TestMQTTLogic(unittest.TestCase):
    def test_topic_calculator_calculate(self):
        """Validate string manipulation for dynamic MQTT topics based on UI hierarchy."""
        calc = TopicCalculator(base_topic="OPEN-AIR")
        
        # Test basic formatting
        topic = calc.calculate("volume", "MainTab")
        self.assertEqual(topic, "OPEN-AIR/MainTab/volume")
        
        # Test stripping layout/structural tokens
        topic_with_extra = calc.calculate("gui/knob1", "display/Tab1")
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
