import os
import sys
import subprocess

def ensure_compiled():
    try:
        import oaptpparser_rs
        return
    except ImportError:
        pass
    
    print("🦀 Compiling oaptpparser_rs...")
    crate_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        subprocess.run([sys.executable, "-m", "maturin", "develop", "--release"], cwd=crate_dir, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to compile oaptpparser_rs: {e}")
        raise e
