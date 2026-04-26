#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

# .github/scripts/build_rust_modules.py
# Author: Gemini CLI
# Version: 20260412.1300.1
#
# Description: Builds and installs the centralized Rust core (oaRustCore).

def main():
    project_root = Path(__file__).parent.parent.parent
    rust_core_dir = project_root / "oaRustCore"

    if not rust_core_dir.exists():
        print("✅ No centralized Rust core (oaRustCore) found. Skipping build.")
        return

    print(f"Building and installing centralized Rust core: {rust_core_dir.name}")

    env = os.environ.copy()
    env["PIP_BREAK_SYSTEM_PACKAGES"] = "1"

    try:
        # We use 'maturin develop' for native performance
        # Using '--release' for production-level speed
        subprocess.check_call(["maturin", "develop", "--release"],
                              cwd=rust_core_dir, env=env)
        print(f"✅ Success: {rust_core_dir.name} built and installed.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {rust_core_dir.name} with error: {e}")
        sys.exit(1)

    print("\n🎉 Native Rust pipeline built successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
