# oaRustCore/Tests/test_integrity.py
# Author: Gemini CLI (Collaborator)
# Version: 20260412.1400.1
#
# Description: Checks for legacy Rust artifacts (Cargo.toml, target/, .so files)
#              in the project that should have been migrated to oaRustCore.

import unittest
import os
import pathlib

class TestRustIntegrity(unittest.TestCase):
    """
    Ensures that the project structure is clean and that all Rust logic 
    has been correctly consolidated into 'oaRustCore'.
    """

    def setUp(self):
        """Resolves the project root and the native core directory."""
        self.project_root = pathlib.Path(__file__).parent.parent.parent
        self.rust_core_dir = self.project_root / "oaRustCore"
        self.ignored_dirs = {
            'oaDataLogs', 'oaDataCache', 'oaDataRunningFiles', 
            '.git', '.pytest_cache', '__pycache__', 'target', 
            'oaRustCore' # The current core is allowed to have artifacts
        }

    def test_legacy_cargo_purge(self):
        """Check: Verify no legacy Cargo.toml files exist outside of 'oaRustCore'."""
        stray_cargo_files = []
        for root, dirs, files in os.walk(self.project_root):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]
            
            if 'Cargo.toml' in files:
                rel_path = pathlib.Path(root).relative_to(self.project_root)
                if not str(rel_path).startswith("oaRustCore"):
                    stray_cargo_files.append(str(rel_path))

        if stray_cargo_files:
            error_message = f"❌ [FAILURE] Found {len(stray_cargo_files)} stray 'Cargo.toml' files that must be purged:\n"
            for f in stray_cargo_files:
                error_message += f"  - {f}\n"
            error_message += "💡 Hint: These legacy paths should have been cleaned by the migration script."
            self.fail(error_message)
        else:
            print("✅ [SUCCESS] All legacy 'Cargo.toml' files have been purged.")

    def test_legacy_target_purge(self):
        """Check: Verify no legacy 'target/' directories exist outside of 'oaRustCore'."""
        stray_target_dirs = []
        for root, dirs, files in os.walk(self.project_root):
            # Prune ignored directories
            if 'target' in dirs:
                rel_path = pathlib.Path(root).relative_to(self.project_root)
                if not str(rel_path).startswith("oaRustCore"):
                    stray_target_dirs.append(os.path.join(rel_path, "target"))
            
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]

        if stray_target_dirs:
            error_message = f"❌ [FAILURE] Found {len(stray_target_dirs)} stray 'target/' build artifacts:\n"
            for d in stray_target_dirs:
                error_message += f"  - {d}\n"
            error_message += "💡 Hint: These are taking up massive disk space and must be purged."
            self.fail(error_message)
        else:
            print("✅ [SUCCESS] No loose build artifacts detected.")

    def test_compiled_library_linkage(self):
        """Check: Verify that native extensions (.so) are not residing in legacy paths."""
        stray_so_files = []
        for root, dirs, files in os.walk(self.project_root):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]
            
            for f in files:
                if f.endswith(".so") or (f.endswith(".pyd") and os.name == 'nt'):
                    rel_path = pathlib.Path(root).relative_to(self.project_root)
                    if not str(rel_path).startswith("oaRustCore"):
                        stray_so_files.append(os.path.join(rel_path, f))

        if stray_so_files:
            error_message = f"❌ [FAILURE] Found {len(stray_so_files)} loose compiled libraries:\n"
            for f in stray_so_files:
                error_message += f"  - {f}\n"
            error_message += "💡 Hint: Compiled libraries should reside only in the build core or site-packages."
            self.fail(error_message)
        else:
            print("✅ [SUCCESS] No loose compiled extensions detected.")

if __name__ == "__main__":
    unittest.main()
