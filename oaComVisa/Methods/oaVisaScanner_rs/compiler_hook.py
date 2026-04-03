import os
import shutil
import subprocess
import sys
import importlib

def ensure_compiled():
    try:
        import oavisascanner_rs
        return
    except ImportError:
        pass

    module_dir = os.path.dirname(__file__)
    venv_site = "/home/anthony/.venv/lib/python3.12/site-packages"
    venv_python = "/home/anthony/.venv/bin/python"

    if venv_site not in sys.path:
        sys.path.append(venv_site)
        try:
            import oavisascanner_rs
            return
        except ImportError:
            pass

    # Aggressively clean up corrupted installations
    if os.path.exists(venv_site):
        for item in os.listdir(venv_site):
            if item.startswith("~") and "oavisascanner_rs" in item:
                path = os.path.join(venv_site, item)
                print(f"Removing corrupted installation artifact: {path}")
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)

    env = os.environ.copy()
    env["PIP_BREAK_SYSTEM_PACKAGES"] = "1"

    # Try to uninstall the package first using venv python
    if os.path.exists(venv_python):
        subprocess.run([venv_python, "-m", "pip", "uninstall", "-y", "oavisascanner_rs"], cwd=module_dir, check=False, env=env)
    else:
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "oavisascanner_rs"], cwd=module_dir, check=False, env=env)

    has_so = any(f.endswith('.so') or f.endswith('.pyd') or f.endswith('.dylib') for f in os.listdir(module_dir))
    if not has_so:
        print(f"[{module_dir}] Native binary not found. Compiling via Cargo...")
        try:
            python_exec = venv_python if os.path.exists(venv_python) else sys.executable
            subprocess.run([python_exec, "-m", "maturin", "develop", "--release"], cwd=module_dir, check=True, env=env)
            print("Compilation successful.")
            importlib.invalidate_caches()
            import oavisascanner_rs
        except subprocess.CalledProcessError:
            print("CRITICAL: Failed to compile Rust extension. Ensure Rust/Cargo is installed.")
            raise RuntimeError("Compilation failed")
        except ImportError as e:
            print(f"CRITICAL: Failed to import compiled module: {e}")
            raise RuntimeError("Import failed")
