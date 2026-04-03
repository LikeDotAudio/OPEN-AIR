import os
import shutil
import subprocess
import sys
import importlib

def build():
    """Build the Rust extension using maturin."""
    try:
        import oalogginggate_rs
        return
    except ImportError:
        pass

    module_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"🦀 [RUST] Building oalogginggate_rs in {module_dir}...")
    venv_site = "/home/anthony/.venv/lib/python3.12/site-packages"
    venv_python = "/home/anthony/.venv/bin/python"

    if venv_site not in sys.path:
        sys.path.append(venv_site)
        try:
            import oalogginggate_rs
            return
        except ImportError:
            pass

    # Aggressively clean up corrupted installations
    if os.path.exists(venv_site):
        for item in os.listdir(venv_site):
            if item.startswith("~") and "oalogginggate_rs" in item:
                path = os.path.join(venv_site, item)
                print(f"Removing corrupted installation artifact: {path}")
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)

    env = os.environ.copy()
    env["PIP_BREAK_SYSTEM_PACKAGES"] = "1"
    
    try:
        python_exec = venv_python if os.path.exists(venv_python) else sys.executable
        # Try to uninstall the package first to avoid issues with partial installations
        subprocess.run([python_exec, "-m", "pip", "uninstall", "-y", "oalogginggate_rs"], cwd=module_dir, check=False, env=env)
        # We use maturin develop to install it in the current environment
        subprocess.check_call([python_exec, "-m", "maturin", "develop", "--release"], cwd=module_dir, env=env)
        print("✅ [RUST] Build successful.")
        importlib.invalidate_caches()
        import oalogginggate_rs
    except Exception as e:
        print(f"❌ [RUST] Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build()