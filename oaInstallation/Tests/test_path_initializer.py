import unittest
import os
import shutil
from pathlib import Path
from oaOchestration.path_initializer import initialize_paths

class TestPathInitializer(unittest.TestCase):
    def test_initialize_paths(self):
        """Check if required system directories are created."""
        # Use initialize_paths to get project root and running state dir
        root, running_dir = initialize_paths()
        
        self.assertTrue(root.exists(), "Project root does not exist")
        self.assertTrue(running_dir.exists(), "Running state directory does not exist")
        
        # Check for specific refactored directories sibling to the hidden cache
        expected_dirs = [
            root / "oaDataLogs",
            root / "oaDataCache",
            root / "oaDataSNMP",
            root / "oaDataSplinks"
        ]
        
        for d in expected_dirs:
            self.assertTrue(d.exists(), f"Refactored directory '{d.name}' missing")

if __name__ == "__main__":
    unittest.main()
