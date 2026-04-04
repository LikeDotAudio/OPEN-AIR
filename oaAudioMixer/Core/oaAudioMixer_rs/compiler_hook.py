# oaAudioMixer/Core/oaAudioMixer_rs/compiler_hook.py
# Author: Gemini (Collaborator)
# Version: 20260403.2300.22
#
# Description: Helper to ensure the Rust PyO3 module is compiled.

import subprocess
import sys
import os
import shutil
import re
from pathlib import Path

def ensure_compiled():
    """
    Ensures the Rust PyO3 module for oaAudioMixer_rs is compiled.
    """
    rust_project_path = Path(__file__).parent
    
    # print("sys.path BEFORE maturin:", sys.path) # DEBUG
    
    print(f"📡 [RUST COMPILER] Ensuring oaAudioMixer_rs is compiled in develop mode...")
    try:
        # Use maturin develop --release to compile and install into the current environment
        result = subprocess.run(
            [sys.executable, "-m", "maturin", "develop", "--release"],
            cwd=rust_project_path,
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ Rust oaAudioMixer_rs compiled successfully.")
        if result.stdout:
            print(f"STDOUT:
{result.stdout}")
        if result.stderr:
            print(f"STDERR:
{result.stderr}")

        # Maturing develop should handle adding the module to a discoverable path.
        # If it's still not found, there might be environment activation issues.
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to compile Rust oaAudioMixer_rs: {e}")
        # Use f-strings with explicit newlines for error messages
        print(f"STDOUT:
{e.stdout}")
        print(f"STDERR:
{e.stderr}")
        raise
    except FileNotFoundError:
        print("❌ 'maturin' command not found. Please install maturin (pip install maturin).")
        raise
        
    # print("sys.path AFTER maturin (and manual adjustment):", sys.path) # DEBUG
