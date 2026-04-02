# oaTests/Methods/oaLogProcessor_rs/compiler_hook.py
# Author: Gemini Iron Oxide Architect
# Version: 20260401.2330.1

import os
import subprocess
import sys

def build():
    """Build the Rust extension using maturin."""
    module_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"🦀 [RUST] Building oalogprocessor_rs in {module_dir}...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "maturin", "develop", "--release"], cwd=module_dir)
        print("✅ [RUST] Build successful.")
    except Exception as e:
        print(f"❌ [RUST] Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build()
