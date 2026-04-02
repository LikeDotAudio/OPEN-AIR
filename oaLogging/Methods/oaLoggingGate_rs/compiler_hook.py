# oaLogging/Methods/oaLoggingGate_rs/compiler_hook.py
# Author: Gemini Architect
# Version: 20260401.1955.1

import os
import subprocess
import sys

def build():
    """Build the Rust extension using maturin."""
    module_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"🦀 [RUST] Building oalogginggate_rs in {module_dir}...")
    
    try:
        # We use maturin develop to install it in the current environment
        subprocess.check_call([sys.executable, "-m", "maturin", "develop", "--release"], cwd=module_dir)
        print("✅ [RUST] Build successful.")
    except Exception as e:
        print(f"❌ [RUST] Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build()
