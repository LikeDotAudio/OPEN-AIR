
import os
import re

TEMPLATE = """# {file_path}
# Author: Gemini (Collaborator)
# Version: 20260406.1300.2
#
# Description: Compiler hook for {module_name}. 
#              Strictly uses system python and user site-packages. No virtual environments.

import os
import subprocess
import sys
import importlib
import glob

def ensure_compiled():
    \"\"\"Build the Rust extension and install to user site-packages.\"\"\"
    try:
        import {module_name}
        return
    except ImportError:
        pass

    user_site = os.path.expanduser(f\"~/.local/lib/python{{sys.version_info.major}}.{{sys.version_info.minor}}/site-packages\")
    if user_site not in sys.path:
        sys.path.append(user_site)
        try:
            import {module_name}
            return
        except ImportError:
            pass

    module_dir = os.path.dirname(os.path.abspath(__file__))
    env = os.environ.copy()
    env[\"PIP_BREAK_SYSTEM_PACKAGES\"] = \"1\"
    
    try:
        python_exec = sys.executable
        # Build the wheel
        subprocess.check_call([\"maturin\", \"build\", \"--release\", \"--interpreter\", python_exec], 
                              cwd=module_dir, env=env, 
                              stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        
        # Install the wheel (handle potential name normalization)
        wheels = glob.glob(os.path.join(module_dir, \"target\", \"wheels\", \"{module_name}-*.whl\"))
        if not wheels:
            # Try with hyphens replaced by underscores or vice versa
            normalized = \"{module_name}\".replace(\"_\", \"-\")
            wheels = glob.glob(os.path.join(module_dir, \"target\", \"wheels\", f\"{{normalized}}-*.whl\"))
        
        if not wheels:
            # Last resort: just look for any wheel in the target/wheels dir
            wheels = glob.glob(os.path.join(module_dir, \"target\", \"wheels\", \"*.whl\"))

        if wheels:
            subprocess.check_call([python_exec, \"-m\", \"pip\", \"install\", \"--user\", \"--force-reinstall\", wheels[0]], 
                                  cwd=module_dir, env=env, 
                                  stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            
            importlib.invalidate_caches()
            import {module_name}
    except Exception:
        # Graceful failure to allow parent to handle fallback
        pass

if __name__ == \"__main__\":
    ensure_compiled()
"""

def find_module_name(dir_path):
    # Try pyproject.toml first
    pyproject = os.path.join(dir_path, "pyproject.toml")
    if os.path.exists(pyproject):
        with open(pyproject, "r") as f:
            content = f.read()
            # Look for module-name in [tool.maturin]
            match = re.search(r'module-name\s*=\s*\"([^\"]+)\"', content)
            if match:
                return match.group(1)
            # Look for name in [project]
            match = re.search(r'^name\s*=\s*\"([^\"]+)\"', content, re.MULTILINE)
            if match:
                return match.group(1).lower().replace("-", "_")

    # Try Cargo.toml
    cargo = os.path.join(dir_path, "Cargo.toml")
    if os.path.exists(cargo):
        with open(cargo, "r") as f:
            content = f.read()
            match = re.search(r'^name\s*=\s*\"([^\"]+)\"', content, re.MULTILINE)
            if match:
                return match.group(1).lower().replace("-", "_")
    
    return None

def main():
    hooks = []
    for root, dirs, files in os.walk("."):
        if "compiler_hook.py" in files:
            hooks.append(os.path.join(root, "compiler_hook.py"))
    
    print(f"Found {len(hooks)} compiler hooks.")
    
    for hook_path in hooks:
        dir_path = os.path.dirname(hook_path)
        module_name = find_module_name(dir_path)
        
        if not module_name:
            print(f"Skipping {hook_path}: Could not determine module name.")
            continue
        
        print(f"Updating {hook_path} for module {module_name}...")
        
        # We use the relative path from the project root for the header
        rel_hook_path = os.path.relpath(hook_path, ".")
        
        new_content = TEMPLATE.format(file_path=rel_hook_path, module_name=module_name)
        
        with open(hook_path, "w") as f:
            f.write(new_content)

if __name__ == "__main__":
    main()
