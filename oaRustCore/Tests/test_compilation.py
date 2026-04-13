# oaRustCore/Tests/test_compilation.py
# Author: Gemini CLI (Collaborator)
# Version: 20260412.1400.1
#
# Description: Verifies that the centralized Rust core (oaRustCore) compiles 
#              and installs correctly using the maturin develop pipeline.

import unittest
import os
import sys
import subprocess
from pathlib import Path

class TestRustCoreCompilation(unittest.TestCase):
    """
    Automated verification of the centralized native pipeline.
    Ensures that 'maturin develop' succeeds for the master oaRustCore crate.
    """

    def setUp(self):
        """Resolves the project root and the native core directory."""
        self.project_root = Path(__file__).parent.parent.parent
        self.rust_core_dir = self.project_root / "oaRustCore"

    def test_maturin_compilation(self):
        """Check: Verify 'maturin develop' succeeds for the master core."""
        if not self.rust_core_dir.exists():
            self.skipTest("❌ [SKIP] oaRustCore directory not found.")

        print(f"\n--- Compiling Central Rust Core: {self.rust_core_dir} ---")
        
        env = os.environ.copy()
        env["PIP_BREAK_SYSTEM_PACKAGES"] = "1"
        
        try:
            # We use 'maturin develop' to link the shared library into the python path
            # This is the "single call" mentioned in the orchestrator mandate.
            result = subprocess.run(
                [sys.executable, "-m", "maturin", "develop"], 
                cwd=str(self.rust_core_dir), 
                env=env,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                error_msg = f"❌ [FAILURE] Native compilation failed:\n"
                error_msg += f"STDOUT: {result.stdout}\n"
                error_msg += f"STDERR: {result.stderr}"
                self.fail(error_msg)
            
            print("✅ [SUCCESS] oaRustCore compiled and installed successfully.")
            
            # Verify the module is importable
            try:
                import oaRustCore
                print(f"📦 [VERIFY] Module '{oaRustCore.__name__}' is active and importable.")
            except ImportError as e:
                self.fail(f"❌ [FAILURE] Module was compiled but cannot be imported: {e}")

        except FileNotFoundError:
            self.fail("❌ [FAILURE] 'maturin' is not installed or not in the system PATH.")

if __name__ == "__main__":
    unittest.main()
