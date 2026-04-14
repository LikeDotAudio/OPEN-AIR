# oaTests/Tests/test_rust_compilation.py
# Author: Gemini CLI (Collaborator)
# Version: 20260403.2215.1
#
# Description: Automated compilation tests for all Rust (Cargo) containers in the project.
# Discovers each Cargo.toml and runs 'cargo check' to ensure syntax and dependency integrity.

import unittest
import os
import subprocess
import pathlib

class TestRustCompilation(unittest.TestCase):
    """
    Test suite to verify that every Rust module in the OPEN-AIR project 
    can successfully compile or at least passes 'cargo check'.
    """

    def _find_cargo_projects(self):
        """
        Dynamically locate all Cargo.toml files in the project root, 
        excluding known data and log directories.
        """
        project_root = pathlib.Path(__file__).parent.parent.parent
        cargo_files = []
        
        # Directories to ignore
        ignored_dirs = {
            'oaDataLogs/Audits', 'oaDataCache', 'oaDataLogs', 
            'oaDataSplinks', 'oaDataRunningFiles', '.git', '.pytest_cache', 
            'target', '__pycache__'
        }

        for root, dirs, files in os.walk(project_root):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            
            if 'Cargo.toml' in files:
                cargo_files.append(pathlib.Path(root))
        
        return sorted(cargo_files)

    def test_rust_compilation(self):
        """
        Check: Iterate through all discovered Cargo projects and run 'cargo check'.
        """
        cargo_projects = self._find_cargo_projects()
        
        if not cargo_projects:
            self.skipTest("No Cargo.toml files found in the project.")

        for project_dir in cargo_projects:
            with self.subTest(project=project_dir.name, path=str(project_dir)):
                # We use 'cargo check' as it is faster than 'cargo build' but 
                # still verifies that the code is syntactically correct and 
                # that dependencies are resolvable.
                
                # Pre-run: Update dependencies if needed (optional, could be slow)
                # We assume the environment is set up and we just want to verify compilation.
                
                result = subprocess.run(
                    ["cargo", "check", "--quiet"],
                    cwd=project_dir,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    error_message = f"Failed to compile Rust project at {project_dir}\n"
                    error_message += f"STDOUT: {result.stdout}\n"
                    error_message += f"STDERR: {result.stderr}"
                    self.fail(error_message)

if __name__ == "__main__":
    unittest.main()
