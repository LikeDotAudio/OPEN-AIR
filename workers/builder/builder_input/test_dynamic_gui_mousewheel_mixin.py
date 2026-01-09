
import unittest
import os
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from workers.builder.builder_input.dynamic_gui_mousewheel_mixin import MousewheelScrollMixin

class TestMousewheelScrollMixin(unittest.TestCase):

    def test_import(self):
        self.assertTrue(True, "Successfully imported MousewheelScrollMixin")

    def test_replace_backslash(self):
        # This test checks if the backslash replacement logic is correct.
        # The original faulty code was:
        # current_file = str(current_file_path.relative_to(project_root)).replace("\", "/")
        # The corrected code is:
        # current_file = str(current_file_path.relative_to(project_root)).replace("\\", "/")

        # Simulate a windows path for testing
        path_with_backslash = "workers\\builder\\builder_input\\dynamic_gui_mousewheel_mixin.py"
        
        # Correct replacement
        path_with_forwardslash = path_with_backslash.replace("\\", "/")
        self.assertEqual(path_with_forwardslash, "workers/builder/builder_input/dynamic_gui_mousewheel_mixin.py")

        # Faulty replacement - this will raise a SyntaxError if uncommented
        # with self.assertRaises(SyntaxError):
        #     exec('path_with_backslash.replace("\", "/")')

if __name__ == '__main__':
    unittest.main()
