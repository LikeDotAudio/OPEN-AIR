import sys
import os
import subprocess
import importlib

def ensure_compiled():
    try:
        import oablueprintparser_rs
        return
    except ImportError:
        pass
    
    # Check if we are running in the system python but have a venv available
    venv_site = "/home/anthony/.venv/lib/python3.12/site-packages"
    if venv_site not in sys.path:
        sys.path.append(venv_site)
        try:
            import oablueprintparser_rs
            return
        except ImportError:
            pass

    print("🦀 Compiling oablueprintparser_rs...")
    crate_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Force use of the venv python for compilation to ensure it goes to the right place
    venv_python = "/home/anthony/.venv/bin/python"
    
    try:
        subprocess.run([venv_python, "-m", "maturin", "develop", "--release"], cwd=crate_dir, check=True)
        importlib.invalidate_caches()
        # Double check import after compilation
        import oablueprintparser_rs
    except (subprocess.CalledProcessError, ImportError) as e:
        print(f"❌ Failed to compile or import oablueprintparser_rs: {e}")
        # Try one last fallback to just importing it if it somehow worked
        try:
            importlib.invalidate_caches()
            import oablueprintparser_rs
        except ImportError:
            raise e
