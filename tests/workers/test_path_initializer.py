import unittest
import os
import shutil
from pathlib import Path
from workers.initialization.path_initializer import initialize_paths

class TestPathInitializer(unittest.TestCase):
    def test_initialize_paths(self):
        """Check if required system directories are created."""
        # Use initialize_paths to get project root and data dir
        root, data_dir = initialize_paths()
        
        self.assertTrue(root.exists(), "Project root does not exist")
        self.assertTrue(data_dir.exists(), "Data directory does not exist")
        
        # Check for specific folders in the DATA tree
        expected_folders = ["cache", "debug", "state"]
        for folder in expected_folders:
            folder_path = data_dir / folder
            self.assertTrue(folder_path.exists(), f"DATA folder '{folder}' missing")

if __name__ == "__main__":
    unittest.main()
