import os, subprocess, sys

def ensure_compiled():
    module_dir = os.path.dirname(__file__)
    # Check for .so or .pyd (Windows)
    has_so = any(f.endswith('.so') or f.endswith('.pyd') or f.endswith('.dylib') for f in os.listdir(module_dir))
    if not has_so:
        print(f"[{module_dir}] Native binary not found. Compiling via Cargo...")
        try:
            # We use 'maturin develop' to build and install in the current directory
            # For a portable solution, we'd use 'maturin build' and move the binary
            # but following the existing pattern:
            subprocess.run(["maturin", "develop", "--release"], cwd=module_dir, check=True)
            print("Compilation successful.")
        except subprocess.CalledProcessError:
            print("CRITICAL: Failed to compile Rust extension. Ensure Rust/Cargo is installed.")
            raise RuntimeError("Compilation failed")
