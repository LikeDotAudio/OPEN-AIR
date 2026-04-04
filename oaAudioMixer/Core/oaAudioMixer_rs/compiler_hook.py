# oaAudioMixer/Core/oaAudioMixer_rs/compiler_hook.py
# Author: Gemini (Collaborator)
# Version: 20260404.0035.36
#
# Description: Helper to ensure the Rust PyO3 module is compiled and its path added to sys.path.

import subprocess
import sys
import os
import shutil
from pathlib import Path

def ensure_compiled():
    """
    Ensures the Rust PyO3 module for oaAudioMixer_rs is compiled
    and its path is added to sys.path if not already present.
    Only recompiles if source files are newer than the binary.
    """
    rust_project_path = Path(__file__).parent
    target_dir = rust_project_path / "target" / "release"
    module_name = "oaaudiomixer_rs"
    
    # Determine the target library path
    if sys.platform.startswith("linux"):
        src_lib = target_dir / f"lib{module_name}.so"
        dst_lib = target_dir / f"{module_name}.so"
    elif sys.platform == "darwin":
        src_lib = target_dir / f"lib{module_name}.dylib"
        dst_lib = target_dir / f"{module_name}.so"
    elif sys.platform == "win32":
        src_lib = target_dir / f"{module_name}.dll"
        dst_lib = target_dir / f"{module_name}.pyd"
    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")

    # Check if we need to recompile
    needs_recompile = not dst_lib.exists()
    
    if not needs_recompile:
        # Check if any source file is newer than the binary
        bin_mtime = dst_lib.stat().st_mtime
        
        # Check Cargo.toml
        if (rust_project_path / "Cargo.toml").stat().st_mtime > bin_mtime:
            needs_recompile = True
        
        # Check src directory recursively
        if not needs_recompile:
            for root, dirs, files in os.walk(rust_project_path / "src"):
                for file in files:
                    if Path(os.path.join(root, file)).stat().st_mtime > bin_mtime:
                        needs_recompile = True
                        break
                if needs_recompile:
                    break

    if needs_recompile:
        print(f"📡 [RUST COMPILER] Recompiling oaAudioMixer_rs in release mode...")
        try:
            subprocess.run(
                ["cargo", "build", "--release"],
                cwd=rust_project_path,
                capture_output=True,
                text=True,
                check=True
            )
            print("✅ Rust oaAudioMixer_rs built successfully.")
            
            if src_lib.exists():
                if src_lib != dst_lib:
                    shutil.copy2(src_lib, dst_lib)
            else:
                raise FileNotFoundError(f"Could not find compiled library at {src_lib}")

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to build Rust oaAudioMixer_rs: {e}")
            if e.stderr:
                print("STDERR:")
                print(e.stderr)
            raise
        except FileNotFoundError:
            print("❌ 'cargo' command not found. Please install Rust and Cargo.")
            raise
    # else:
    #    print(f"📡 [RUST COMPILER] oaAudioMixer_rs is up to date.")

    # Add target/release to sys.path if not already present
    if str(target_dir) not in sys.path:
        sys.path.insert(0, str(target_dir))
