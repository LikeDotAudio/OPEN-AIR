import sys
import os
import subprocess
import importlib
import shutil

def ensure_compiled():
    try:
        from oasplinkcore_rs import SplinkPipeline
        return
    except ImportError:
        pass
    
    venv_site = "/home/anthony/.venv/lib/python3.12/site-packages"
    if venv_site not in sys.path:
        sys.path.append(venv_site)
        try:
            from oasplinkcore_rs import SplinkPipeline
            return
        except ImportError:
            pass

    print("🦀 Compiling oasplinkcore_rs...")
    crate_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = "/home/anthony/.venv/bin/python"
    env = os.environ.copy()
    env["PIP_BREAK_SYSTEM_PACKAGES"] = "1"

    if os.path.exists(venv_python):
        # Try to uninstall from venv
        subprocess.run([venv_python, "-m", "pip", "uninstall", "-y", "oasplinkcore_rs"], cwd=crate_dir, check=False, env=env)
    
    # Also attempt to uninstall from system/user python to prevent shadowing
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "oasplinkcore_rs", "--break-system-packages"], cwd=crate_dir, check=False, env=env)
    
    try:
        python_exec = venv_python if os.path.exists(venv_python) else sys.executable
        subprocess.run([python_exec, "-m", "maturin", "develop", "--release"], cwd=crate_dir, check=True, env=env)
        importlib.invalidate_caches()
        from oasplinkcore_rs import SplinkPipeline
    except (subprocess.CalledProcessError, ImportError) as e:
        print(f"❌ Failed to compile or import oasplinkcore_rs: {e}")
        raise e

if __name__ == "__main__":
    ensure_compiled()
