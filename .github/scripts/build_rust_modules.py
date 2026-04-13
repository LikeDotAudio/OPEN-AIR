#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

# FolderName/build_rust_modules.py
# Author: Gemini CLI
# Version: 20260412.1200.1
#
# Description: Finds all Rust-based modules (pyproject.toml with maturin) and builds/installs them.

def main():
    project_root = Path(__file__).parent.parent.parent
    
    # Find all pyproject.toml files that use maturin
    pyproject_files = list(project_root.glob("**/pyproject.toml"))
    
    maturin_modules = []
    for f in pyproject_files:
        with open(f, 'r') as file:
            content = file.read()
            if 'build-backend = "maturin"' in content or 'requires = ["maturin' in content:
                maturin_modules.append(f.parent)
                
    if not maturin_modules:
        print("✅ No Rust modules requiring maturin found.")
        return

    print(f"Found {len(maturin_modules)} Rust modules. Building and installing...")
    
    env = os.environ.copy()
    env["PIP_BREAK_SYSTEM_PACKAGES"] = "1"
    
    failed_modules = []
    for module_dir in maturin_modules:
        print(f"\n--- Building: {module_dir.relative_to(project_root)} ---")
        try:
            # We use 'maturin develop' as recommended in GEMINI.md, but 'pip install .' is safer for CI
            # GEMINI.md says: prefer 'maturin develop --release'
            subprocess.check_call(["maturin", "develop", "--release"], 
                                  cwd=module_dir, env=env)
            print(f"✅ Success: {module_dir.name}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed: {module_dir.name} with error: {e}")
            failed_modules.append(str(module_dir.relative_to(project_root)))
            
    if failed_modules:
        print("\n❌ [BUILD FAILURE] Some Rust modules failed to build:")
        for mod in failed_modules:
            print(f"  - {mod}")
        sys.exit(1)
    else:
        print("\n🎉 All Rust modules built and installed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
