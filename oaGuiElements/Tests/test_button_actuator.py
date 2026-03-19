import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiElements.Core.buttons.button_actuator.button_actuator import ActuatorButton, BuilderButtonActuatorCreator

class TestButtonActuator(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
        
        self.config = {
            "label": "Test Actuator",
            "path": "test/actuator",
            "width": 100,
            "height": 50
        }
        self.mirror_engine = MagicMock()
        self.router = MagicMock()
        self.builder = MagicMock()
        
        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.subscriber_router = self.router
        self.context.base_mqtt_topic_from_path = "test/topic"
        self.context.builder_instance = self.builder

    def test_actuator_button_initialization(self):
        """Goal: Verify that the ActuatorButton initializes correctly."""
        button = ActuatorButton(
            parent=self.root,
            config=self.config,
            path="test/actuator",
            state_mirror_engine=self.mirror_engine,
            base_mqtt_topic="test/topic",
            subscriber_router=self.router,
            builder_instance=self.builder
        )
        self.assertEqual(button.path, "test/actuator")
        self.assertEqual(button.label, "Test Actuator")

    def test_builder_creator_make(self):
        """Goal: Verify that BuilderButtonActuatorCreator creates an ActuatorButton."""
        creator = BuilderButtonActuatorCreator()
        button = creator.make_button_actuator(
            parent_widget=self.root,
            config_data=self.config,
            context=self.context
        )
        self.assertIsInstance(button, ActuatorButton)

    def tearDown(self):
        if hasattr(self.root, "destroy"):
            self.root.destroy()

if __name__ == "__main__":
    unittest.main()
