import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiElements.Core.input.json_tree.json_tree import BuilderDataJsonTreeCreator, JsonTreeWidget

class TestJsonTree(unittest.TestCase):

    def setUp(self):
        self.patchers = []
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
            self.root.winfo_exists.return_value = True
            
            # Patch variables if Tk fails
            self.patchers.append(patch("tkinter.StringVar", return_value=MagicMock()))
            self.patchers.append(patch("tkinter.DoubleVar", return_value=MagicMock()))
            self.patchers.append(patch("tkinter.BooleanVar", return_value=MagicMock()))
            self.patchers.append(patch("tkinter.IntVar", return_value=MagicMock()))
            
            self.patchers.append(patch('tkinter.ttk.Treeview', return_value=MagicMock()))
            self.patchers.append(patch('tkinter.ttk.Scrollbar', return_value=MagicMock()))
            self.patchers.append(patch('tkinter.Canvas', return_value=MagicMock()))
            self.patchers.append(patch('tkinter.Frame', return_value=MagicMock()))
            for p in self.patchers:
                p.start()
        self.config = {'label_active': 'Test Tree', 'path': 'test/tree', 'json_source': 'oaGuiElements/Core/input/json_tree/sample.json'}
        self.mirror_engine = MagicMock()
        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.base_mqtt_topic_from_path = 'test/base'
        self.context.builder_instance = MagicMock()

    def test_json_tree_initialization(self):
        try:
            'Goal: Verify that JsonTreeWidget initializes correctly.'
            widget = JsonTreeWidget(parent=self.root, config=self.config, state_mirror_engine=self.mirror_engine, base_mqtt_topic='test/base')
            self.assertTrue(hasattr(widget, 'tree'), "Expected hasattr(widget, 'tree') to be True")
        except Exception as e:
            self.fail(f'Test json tree initialization crashed. Error: {str(e)}')

    def test_builder_creator_make(self):
        try:
            'Goal: Verify that BuilderDataJsonTreeCreator creates a JsonTreeWidget.'
            creator = BuilderDataJsonTreeCreator()
            widget = creator.make_data_json_tree(parent_widget=self.root, config_data=self.config, context=self.context)
            self.assertIsNotNone(widget, 'Expected widget to be not None')
        except Exception as e:
            self.fail(f'Test builder creator make crashed. Error: {str(e)}')

    def tearDown(self):
        if hasattr(self, 'patchers'):
            for p in self.patchers:
                p.stop()
        if hasattr(self.root, 'destroy'):
            self.root.destroy()
if __name__ == '__main__':
    unittest.main()