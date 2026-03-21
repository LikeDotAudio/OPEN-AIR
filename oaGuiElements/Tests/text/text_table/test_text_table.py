import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiElements.Core.text.text_table.text_table import BuilderTextTableCreator

class TestTextTable(unittest.TestCase):

    def setUp(self):
        self.patchers = []
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
            self.root.winfo_exists.return_value = True
            
            # Patch variables
            self.patchers.append(patch("tkinter.StringVar", return_value=MagicMock()))
            
            mock_canvas = MagicMock()
            mock_canvas.winfo_exists.return_value = True
            mock_canvas.__str__.return_value = ".mock_canvas"
            self.patchers.append(patch('tkinter.Canvas', return_value=mock_canvas))
            self.patchers.append(patch('tkinter.ttk.Treeview', return_value=MagicMock()))
            self.patchers.append(patch('tkinter.ttk.Scrollbar', return_value=MagicMock()))
            for p in self.patchers:
                p.start()
        self.config = {'label_active': 'Test Table', 'path': 'test/table', 'headers': ['Col1', 'Col2'], 'data': [['A', 'B'], ['C', 'D']]}
        self.mirror_engine = MagicMock()
        self.mirror_engine.calculate_topic.return_value = 'test/topic'
        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.base_mqtt_topic_from_path = 'test/base'
        self.context.subscriber_router = MagicMock()
        self.context.builder_instance = MagicMock()

    def test_make_text_table(self):
        try:
            'Goal: Verify that BuilderTextTableCreator creates a table widget.'
            creator = BuilderTextTableCreator()
            table_widget = creator.make_text_table(parent_widget=self.root, config_data=self.config, context=self.context)
            self.assertIsNotNone(table_widget, 'Expected table_widget to be not None')
            self.mirror_engine.register_widget.assert_called()
        except Exception as e:
            self.fail(f'Test make text table crashed. Error: {str(e)}')

    def tearDown(self):
        if hasattr(self, 'patchers'):
            for p in self.patchers:
                p.stop()
        if hasattr(self.root, 'destroy'):
            self.root.destroy()
if __name__ == '__main__':
    unittest.main()