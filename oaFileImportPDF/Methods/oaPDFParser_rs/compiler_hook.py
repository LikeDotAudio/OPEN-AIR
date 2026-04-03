import sys
import os
import subprocess
import importlib
import shutil

def ensure_compiled():
    try:
        from oapdfparser_rs.oapdfparser_rs import PDFEngine
        return
    except ImportError:
        pass
    
    # Check if we are running in the system python but have a venv available
    venv_site = "/home/anthony/.venv/lib/python3.12/site-packages"
    if venv_site not in sys.path:
        sys.path.append(venv_site)
        try:
            from oapdfparser_rs.oapdfparser_rs import PDFEngine
            return
        except ImportError:
            pass

    print("🦀 Compiling oapdfparser_rs...")
    crate_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Force use of the venv python for compilation to ensure it goes to the right place
    venv_python = "/home/anthony/.venv/bin/python"
    
    env = os.environ.copy()
    env["PIP_BREAK_SYSTEM_PACKAGES"] = "1"

    # Aggressively clean up corrupted installations
    if os.path.exists(venv_site):
        for item in os.listdir(venv_site):
            if item.startswith("~") and "oapdfparser_rs" in item:
                path = os.path.join(venv_site, item)
                print(f"Removing corrupted installation artifact: {path}")
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)

    # Try to uninstall the package first using venv python
    if os.path.exists(venv_python):
        subprocess.run([venv_python, "-m", "pip", "uninstall", "-y", "oapdfparser_rs"], cwd=crate_dir, check=False, env=env)
    else:
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "oapdfparser_rs"], cwd=crate_dir, check=False, env=env)


    try:
        python_exec = venv_python if os.path.exists(venv_python) else sys.executable
        subprocess.run([python_exec, "-m", "maturin", "develop", "--release"], cwd=crate_dir, check=True, env=env)
        importlib.invalidate_caches()
        # Double check import after compilation
        from oapdfparser_rs.oapdfparser_rs import PDFEngine
    except (subprocess.CalledProcessError, ImportError) as e:
        print(f"❌ Failed to compile or import oapdfparser_rs: {e}")
        # Try one last fallback to just importing it if it somehow worked
        try:
            importlib.invalidate_caches()
            from oapdfparser_rs.oapdfparser_rs import PDFEngine
        except ImportError:
            raise e

if __name__ == "__main__":
    ensure_compiled()
