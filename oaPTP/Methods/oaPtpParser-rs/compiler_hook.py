import sys
import os
import subprocess

def ensure_compiled():
    # 1. Try importing normally
    try:
        import oaptpparser_rs
        return
    except ImportError:
        pass
    
    # 2. Try importing from the target directory directly (no restart required)
    crate_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(crate_dir, "target", "release")
    if target_dir not in sys.path:
        sys.path.insert(0, target_dir)
        
    try:
        import oaptpparser_rs
        return
    except ImportError:
        pass

    print("🦀 Compiling oaptpparser_rs...")
    try:
        # We use 'cargo build --release' instead of maturin for immediate path-based access
        subprocess.run(["cargo", "build", "--release"], cwd=crate_dir, check=True)
        # On Linux, maturin creates oaptpparser_rs.so in target/release
        # We might need to rename it or link it if cargo doesn't produce the right name
        # Actually, cargo with cdylib produces liboaptpparser_rs.so. 
        # Python expects oaptpparser_rs.so
        
        lib_name = "liboaptpparser_rs.so"
        target_name = "oaptpparser_rs.so"
        
        lib_path = os.path.join(target_dir, lib_name)
        target_path = os.path.join(target_dir, target_name)
        
        if os.path.exists(lib_path) and not os.path.exists(target_path):
            os.symlink(lib_name, target_path)
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to compile oaptpparser_rs: {e}")
        raise e
