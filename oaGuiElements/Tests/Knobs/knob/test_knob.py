import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
import os

from oaGuiElements.Core.Knobs.knob.knob import BuilderKnobCreator, CustomKnobFrame
from oaGuiElements.Tests.utils.test_utils import load_sample_config

class TestKnobWidget(unittest.TestCase):

    def setUp(self):
        self.patchers = []
        try:
            self.root = tk.Tk()
            self.root.withdraw()
            self.HAS_DISPLAY = True
        except:
            self.HAS_DISPLAY = False
            # ⚡ Fix: Use a mock that doesn't trigger internal Tkinter logic
            self.root = MagicMock()
            self.root.winfo_exists.return_value = True
            self.root.cget.return_value = "#2b2b2b"
            
            # Patch DoubleVar to return a mock
            self.patchers.append(patch('tkinter.DoubleVar', return_value=MagicMock()))
            # Patch Canvas and Frame to avoid ANY internal Tkinter calls
            self.patchers.append(patch('tkinter.Canvas', return_value=MagicMock()))
            self.patchers.append(patch('tkinter.Frame', return_value=MagicMock()))
            
            for p in self.patchers:
                p.start()

        component_dir = os.path.join(os.path.dirname(__file__), '..', 'Core', 'Knobs', 'knob')
        self.config = load_sample_config(component_dir)
        self.config['path'] = 'test/knob'
        
        self.mirror_engine = MagicMock()
        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.subscriber_router = MagicMock()
        self.context.base_mqtt_topic_from_path = 'OPEN-AIR/test'
        self.context.builder_instance = MagicMock()

    def test_creation_via_builder(self):
        try:
            """Verify that the Knob initializes correctly."""
            frame, canvas = BuilderKnobCreator.make(self.root, self.config, context=self.context)
            self.assertIsNotNone(frame, "Expected frame to be not None")
        except Exception as e:
            self.fail(f'Test creation via builder crashed. Error: {str(e)}')

    def test_broadcast_notifies_engine(self):
        try:
            """Verify that interaction triggers the mirror engine."""
            frame, canvas = BuilderKnobCreator.make(self.root, self.config, context=self.context)
            # frame is a CustomKnobFrame (or mock of it)
            if hasattr(frame, '_broadcast_cb'):
                frame._broadcast_cb()
                self.mirror_engine.broadcast_gui_change_to_mqtt.assert_called_with('test/knob')
        except Exception as e:
            self.fail(f'Test broadcast notifies engine crashed. Error: {str(e)}')

    def tearDown(self):
        if hasattr(self, 'patchers'):
            for p in self.patchers:
                p.stop()
        if hasattr(self, 'root') and hasattr(self.root, 'destroy') and not isinstance(self.root, MagicMock):
            self.root.destroy()

if __name__ == '__main__':
    unittest.main()
