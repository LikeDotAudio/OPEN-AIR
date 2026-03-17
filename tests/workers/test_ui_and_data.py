import unittest
import os
import shutil
import tempfile
import pathlib
from unittest.mock import MagicMock, patch

# --- UI & Widget Construction ---
from managers.Display.parser.layout_parser import LayoutParser
from workers.wysiwyg_editor.core.state import StateManager

# --- Data & Processing Utilities ---
from workers.Showtime.group import group_markers
from workers.wysiwyg_editor.core.file_io_handler import FileIOHandler

class TestUIAndData(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_path = pathlib.Path(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    # --- 4. UI & Widget Construction ---
    def test_layout_parser_scan(self):
        """Recursively find valid UI definition files."""
        # Create a mock directory structure
        gui_dir = self.test_path / "gui_folder"
        gui_dir.mkdir()
        (gui_dir / "gui_main.py").touch()
        (gui_dir / "sub_folder").mkdir()
        (gui_dir / "sub_folder" / "widget.json").touch()
        (gui_dir / "__init__.py").touch()
        
        parser = LayoutParser("1.0")
        # Clear cache to ensure fresh scan
        LayoutParser._scan_cache = {}
        
        # Test scan
        found = parser._scan_for_gui_files(gui_dir)
        self.assertTrue(found, "Failed to find gui files")
        
        # Test __init__ exclusion (if only __init__ exists)
        empty_dir = self.test_path / "empty"
        empty_dir.mkdir()
        (empty_dir / "__init__.py").touch()
        LayoutParser._scan_cache = {}
        found_empty = parser._scan_for_gui_files(empty_dir)
        self.assertFalse(found_empty, "Should ignore __init__.py files")

    def test_state_manager_update(self):
        """Validate that UI changes correctly update the master data state."""
        sm = StateManager()
        sm.reset()
        initial_data = {"ui": {"button": {"color": "red"}}}
        sm.initialize(initial_data)
        
        # Update nested value
        sm.update_state("blue", path="ui.button.color")
        
        current_state = sm.get_state()
        self.assertEqual(current_state["ui"]["button"]["color"], "blue")
        
        # Test non-existent path creation
        sm.update_state(100, path="ui.knob.value")
        self.assertEqual(sm.get_state()["ui"]["knob"]["value"], 100)

    # --- 5. Data & Processing Utilities ---
    def test_marker_logic_grouping(self):
        """Transform a flat list of marker data into a nested Zone/Group dictionary."""
        raw_data = [
            {"NAME": "M1", "ZONE": "Z1", "GROUP": "G1"},
            {"NAME": "M2", "ZONE": "Z1", "GROUP": "G2"},
            {"NAME": "M3", "ZONE": "Z2", "GROUP": "G1"},
            {"NAME": "M4", "ZONE": "Z1", "GROUP": "G1"},
            {"NAME": "M5"} # Missing keys
        ]
        
        grouped = group_markers(raw_data)
        
        # Check structure
        self.assertIn("Z1", grouped)
        self.assertIn("G1", grouped["Z1"])
        self.assertEqual(len(grouped["Z1"]["G1"]), 2)
        
        # Check defaults for missing keys
        self.assertIn("N/A", grouped)
        self.assertIn("N/A", grouped["N/A"])
        self.assertEqual(grouped["N/A"]["N/A"][0]["NAME"], "M5")

    def test_file_io_load(self):
        """Load and parse JSON configuration files."""
        test_json = self.test_path / "test.json"
        data = {"version": "1.0", "settings": {"theme": "dark"}}
        
        import orjson
        with open(test_json, "wb") as f:
            f.write(orjson.dumps(data))
            
        handler = FileIOHandler()
        # Mock StateManager since it's a singleton used inside load_file
        with patch('workers.wysiwyg_editor.core.file_io_handler.state_manager') as mock_sm:
            success = handler.load_file(test_json)
            self.assertTrue(success)
            mock_sm.initialize.assert_called_once()
            # Verify the data passed to initialize
            args, kwargs = mock_sm.initialize.call_args
            self.assertEqual(args[0], data)

if __name__ == "__main__":
    unittest.main()
