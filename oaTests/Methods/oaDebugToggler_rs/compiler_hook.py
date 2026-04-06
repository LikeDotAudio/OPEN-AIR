# oaTests/Methods/oaDebugToggler_rs/compiler_hook.py
# Author: Gemini (Collaborator)
# Version: 20260406.1300.2
#
# Description: Compiler hook for oadebugtoggler_rs. 
#              Strictly uses system python and user site-packages. No virtual environments.

import os
import subprocess
import sys
import importlib
import glob

def ensure_compiled():
    """Build the Rust extension and install to user site-packages."""
    try:
        import oadebugtoggler_rs
        return
    except ImportError:
        pass

    user_site = os.path.expanduser(f"~/.local/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages")
    if user_site not in sys.path:
        sys.path.append(user_site)
        try:
            import oadebugtoggler_rs
            return
        except ImportError:
            pass

    module_dir = os.path.dirname(os.path.abspath(__file__))
    env = os.environ.copy()
    env["PIP_BREAK_SYSTEM_PACKAGES"] = "1"
    
    try:
        python_exec = sys.executable
        # Build the wheel
        subprocess.check_call(["maturin", "build", "--release", "--interpreter", python_exec], 
                              cwd=module_dir, env=env, 
                              stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        
        # Install the wheel (handle potential name normalization)
        wheels = glob.glob(os.path.join(module_dir, "target", "wheels", "oadebugtoggler_rs-*.whl"))
        if not wheels:
            # Try with hyphens replaced by underscores or vice versa
            normalized = "oadebugtoggler_rs".replace("_", "-")
            wheels = glob.glob(os.path.join(module_dir, "target", "wheels", f"{normalized}-*.whl"))
        
        if not wheels:
            # Last resort: just look for any wheel in the target/wheels dir
            wheels = glob.glob(os.path.join(module_dir, "target", "wheels", "*.whl"))

        if wheels:
            subprocess.check_call([python_exec, "-m", "pip", "install", "--user", "--force-reinstall", wheels[0]], 
                                  cwd=module_dir, env=env, 
                                  stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            
            importlib.invalidate_caches()
            import oadebugtoggler_rs
    except Exception:
        # Graceful failure to allow parent to handle fallback
        pass

if __name__ == "__main__":
    ensure_compiled()
