import sys
import os
import subprocess

def ensure_compiled():
    try:
        import oatranslatorcore_rs
        return
    except ImportError:
        pass
    
    print("🦀 Compiling oatranslatorcore_rs...")
    crate_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        subprocess.run([sys.executable, "-m", "maturin", "develop", "--release"], cwd=crate_dir, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to compile oatranslatorcore_rs: {e}")
        raise e
