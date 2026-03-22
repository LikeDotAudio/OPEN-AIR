# radar/test_radar.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiElements.Core.graphing.radar.radar import BuilderDataRadarCreator
from oaGuiElements.Tests.utils.test_utils import load_sample_config
import os

class RadarTestComponent(BuilderDataRadarCreator):

    def __init__(self):
        self.state_mirror_engine = MagicMock()
        self.subscriber_router = MagicMock()
class TestRadarWidget(unittest.TestCase):
    def setUp(self):
        self.patchers = []
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
            self.root.winfo_exists.return_value = True

            # Patch variables
            self.patchers.append(patch("tkinter.IntVar", return_value=MagicMock()))
            self.patchers.append(patch("tkinter.StringVar", return_value=MagicMock()))
            self.patchers.append(patch("tkinter.DoubleVar", return_value=MagicMock()))
            self.patchers.append(patch("tkinter.BooleanVar", return_value=MagicMock()))

            # Patch Canvas
            self.patchers.append(patch("tkinter.Canvas", return_value=MagicMock()))
            self.patchers.append(patch("tkinter.Frame", return_value=MagicMock()))

            for p in self.patchers: p.start()
        component_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'Core', 'graphing', 'radar')
        self.config = load_sample_config(component_dir)
        self.config['path'] = 'test/radar'
        self.radar_creator = RadarTestComponent()
        self.mock_context = MagicMock()
        self.mock_context.state_mirror_engine = self.radar_creator.state_mirror_engine
        self.mock_context.subscriber_router = self.radar_creator.subscriber_router
        self.mock_context.base_mqtt_topic_from_path = 'OPEN-AIR/test'
        self.mock_context.builder_instance = MagicMock()

    def test_creation(self):
        try:
            'Verify that the Radar widget initializes from sample.json.'
            frame = self.radar_creator.make_data_radar(self.root, self.config, context=self.mock_context)
            self.assertIsNotNone(frame, 'Expected frame to be not None')
        except Exception as e:
            self.fail(f'Test creation crashed. Error: {str(e)}')

    def tearDown(self):
        if hasattr(self, 'patchers'):
            for p in self.patchers:
                p.stop()
        if hasattr(self.root, 'destroy'):
            self.root.destroy()
if __name__ == '__main__':
    unittest.main()
