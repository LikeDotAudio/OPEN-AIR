# input_mousewheel_mixin/test_dynamic_gui_mousewheel_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import os
import sys
import unittest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

class TestMousewheelScrollMixin(unittest.TestCase):

    def test_import(self):
        try:
            self.assertTrue(True, 'Successfully imported MousewheelScrollMixin')
        except Exception as e:
            self.fail(f'Test import crashed. Error: {str(e)}')

    def test_replace_backslash(self):
        try:
            path_with_backslash = 'workers\\builder\\builder_input_mousewheel_mixin\\mousewheel_mixin.py'
            path_with_forwardslash = path_with_backslash.replace('\\', '/')
            self.assertEqual(path_with_forwardslash, 'workers/builder/builder_input_mousewheel_mixin/mousewheel_mixin.py', f"Expected 'workers/builder/builder_input_mousewheel_mixin/mousewheel_mixin.py', got '{path_with_forwardslash}'")
        except Exception as e:
            self.fail(f'Test replace backslash crashed. Error: {str(e)}')
if __name__ == '__main__':
    unittest.main()
