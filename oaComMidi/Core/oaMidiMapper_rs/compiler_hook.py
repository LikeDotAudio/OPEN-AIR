# compiler_hook.py
import os
import subprocess
import sys
import shutil
from pathlib import Path

def ensure_compiled():
    """Triggers maturin build if the binary is missing or source changed."""
    crate_dir = Path(__file__).resolve().parent
    release_dir = crate_dir / "target" / "release"
    
    # 1. Run the build
    try:
        subprocess.run(
            ["maturin", "build", "--release"],
            cwd=str(crate_dir),
            check=True,
            capture_output=True
        )
        
        # 2. Locate and rename the .so file (Linux)
        # liboamidimapper_rs.so -> oamidimapper_rs.so
        for f in release_dir.glob("liboamidimapper_rs.*"):
            dest = release_dir / f.name.replace("lib", "", 1)
            shutil.copy2(f, dest)
            
        # 3. Add to sys.path so 'import oamidimapper_rs' works
        if str(release_dir) not in sys.path:
            sys.path.insert(0, str(release_dir))
            
    except Exception as e:
        print(f"⚠️ [RUST-BUILD] Critical failure during compilation: {e}")

if __name__ == "__main__":
    ensure_compiled()
