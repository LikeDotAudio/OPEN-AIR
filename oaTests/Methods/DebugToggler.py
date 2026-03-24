# Methods/DebugToggler.py
# Author: Anthony Peter Kuzub
# Version: 20260323.2105.1
#
# Description: Global utility to toggle, force on, or force off LOCAL_DEBUG 
# and BUILDER_DEBUG flags across the codebase.

import os
import re
from pathlib import Path

def _set_debug_state(project_root, target_state: bool, console_print_func=None):
    """
    Scans the codebase and forces all debug flags to the specified state.
    """
    def log(msg):
        if console_print_func: console_print_func(msg)
        else: print(msg)

    target_state_str = str(target_state)
    action = "ENABLING" if target_state else "DISABLING"
    log(f"⚙️ [CONFIG] Forcing all debug gates to {target_state_str.upper()}...")

    pattern = re.compile(r'^(\s*[A-Z_]+DEBUG\s*=\s*)(True|False)(.*)$', re.MULTILINE)
    
    py_files = []
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', 'node_modules', '__pycache__']]
        for file in files:
            if file.endswith('.py'):
                py_files.append(Path(root) / file)

    files_modified = 0
    flags_changed = 0

    for file_path in py_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not pattern.search(content):
                continue

            replacements_made = 0
            def replacement(match):
                nonlocal replacements_made
                current_value = match.group(2)
                # Only replace if the state is different
                if current_value != target_state_str:
                    replacements_made += 1
                    return f"{match.group(1)}{target_state_str}{match.group(3)}"
                return match.group(0) # Return original match if no change

            new_content = pattern.sub(replacement, content)
            
            if replacements_made > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                files_modified += 1
                flags_changed += replacements_made
        except Exception as e:
            log(f"   ⚠️ Failed to process {file_path.name}: {e}")

    if files_modified > 0:
        log(f"✨ [SUCCESS] {action} complete. Changed {flags_changed} flags across {files_modified} files.")
    else:
        log(f"ℹ️ No state change needed. All debug flags were already {target_state_str.upper()}.")

def force_debug_on(project_root, console_print_func=None):
    """Forces all debug flags to True."""
    _set_debug_state(project_root, True, console_print_func)

def force_debug_off(project_root, console_print_func=None):
    """Forces all debug flags to False."""
    _set_debug_state(project_root, False, console_print_func)

def toggle_debug_flags(project_root, console_print_func=None):
    """
    Searches the codebase for debug flag assignments and toggles them.
    The toggle direction is determined by the state of the first flag found.
    """
    def log(msg):
        if console_print_func: console_print_func(msg)
        else: print(msg)

    log("🔍 [SCAN] Scanning for debug gates to determine current state...")
    pattern = re.compile(r'^\s*[A-Z_]+DEBUG\s*=\s*(True|False)', re.MULTILINE)
    
    current_state_found = None
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', 'node_modules', '__pycache__']]
        for file in files:
            if file.endswith('.py'):
                try:
                    with open(Path(root) / file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    match = pattern.search(content)
                    if match:
                        current_state_found = (match.group(1) == "True")
                        log(f"🔎 Found state reference: DEBUG is {'ON' if current_state_found else 'OFF'}")
                        break
                except Exception:
                    continue
        if current_state_found is not None:
            break

    if current_state_found is None:
        log("🤔 No debug flags found. Assuming OFF state, toggling to ON.")
        force_debug_on(project_root, console_print_func)
    elif current_state_found:
        log("🔄 [TOGGLE] Current state is ON. Forcing all flags to OFF.")
        force_debug_off(project_root, console_print_func)
    else:
        log("🔄 [TOGGLE] Current state is OFF. Forcing all flags to ON.")
        force_debug_on(project_root, console_print_func)


if __name__ == "__main__":
    project_root_path = Path(__file__).resolve().parents[2]
    # Example: force everything ON
    print("--- Forcing ON ---")
    force_debug_on(project_root_path)
    print("\n--- Forcing OFF ---")
    force_debug_off(project_root_path)
    print("\n--- Toggling (will turn ON) ---")
    toggle_debug_flags(project_root_path)
    print("\n--- Toggling (will turn OFF) ---")
    toggle_debug_flags(project_root_path)
