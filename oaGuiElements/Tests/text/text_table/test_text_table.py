# text_table/test_text_table.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiElements.Core.text.text_table.Core.text_table import BuilderTextTableCreator

class TestTextTable(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
        
        self.config = {
            "label_active": "Test Table",
            "path": "test/table",
            "headers": ["Col1", "Col2"],
            "data": [["A", "B"], ["C", "D"]]
        }
        self.mirror_engine = MagicMock()
        self.mirror_engine.calculate_topic.return_value = "test/topic"
        
        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.base_mqtt_topic_from_path = "test/base"
        self.context.subscriber_router = MagicMock()
        self.context.builder_instance = MagicMock()

    def test_make_text_table(self):
        """Goal: Verify that BuilderTextTableCreator creates a table widget."""
        # BUILD
        creator = BuilderTextTableCreator()
        
        # OPERATE
        table_widget = creator.make_text_table(
            parent_widget=self.root,
            config_data=self.config,
            context=self.context
        )
        
        # CHECK
        self.assertIsInstance(table_widget, tk.Canvas)
        self.mirror_engine.register_widget.assert_called()

    def tearDown(self):
        if hasattr(self.root, "destroy"):
            self.root.destroy()

if __name__ == "__main__":
    unittest.main()
