# oaTests/Methods/DebugToggler.py
#
# Global utility to toggle or force debug flags across the OPEN-AIR project.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260327.1415.1

"""
DebugToggler.py - State Management for Conditional Debug Gates.

This utility provides a centralized mechanism to recursively scan the project
tree and modify Python debug constants (LOCAL_DEBUG, BUILDER_DEBUG, DEBUG). 
It is essential for enabling high-velocity forensic analysis without 
manual file traversal.

Responsibilities:
    - Core: Identifies and flips boolean debug gates.
    - Automation: Provides force-on, force-off, and toggle functionality.
"""

import os
import re
from pathlib import Path
from loguru import logger

# --- Native Rust Acceleration ---
from .oaDebugToggler_rs.compiler_hook import ensure_compiled
try:
    ensure_compiled()
    from oadebugtoggler_rs import toggle_debug_flags_rs as toggle_debug_flags_rs_native
    RUST_ENABLED = True
except ImportError:
    RUST_ENABLED = False
    if matrix_log(system="CONFIG", element="DEBUG_TOGGLER", func_name="toggle_debug_flags", message="⚠️ [CONFIG] oadebugtoggler_rs not found. Falling back to slow Python traversal.", level="WARNING"):
        pass
except Exception as e:
    RUST_ENABLED = False
    if matrix_log(system="CONFIG", element="DEBUG_TOGGLER", func_name="toggle_debug_flags", message=f"❌ [CONFIG] Rust debug toggler initialization failed: {e}", level="ERROR"):
        pass

LOCAL_DEBUG = False

def _set_debug_state(project_root, target_state: bool, console_print_func=None):
    """
    Scans the codebase and forces all debug flags to the specified state.
    Utilizes Rust-native acceleration if available.
    """
    def log(msg):
        if console_print_func: console_print_func(msg)
        else: logger.info(msg)

    target_state_str = str(target_state)
    action = "ENABLING" if target_state else "DISABLING"
    log(f"🛠️ [CONFIG] Forcing all debug gates to {target_state_str.upper()}...")

    if RUST_ENABLED:
        try:
            # Call the Rust implementation
            modified = toggle_debug_flags_rs_native(str(project_root), target_state)
            if modified:
                log(f"🚀 [DEPLOY] {action} complete (Native Rust accelerated).")
                return True
            log(f"🛌 [SLEEPING] No state change needed (Native Rust accelerated).")
            return False
        except Exception as e:
            logger.error(f"⚠️ [CONFIG] Rust execution failed: {e}. Falling back to Python...")

    # --- Python Fallback Implementation ---
    # Pattern captures: LOCAL_DEBUG, BUILDER_DEBUG, or generic DEBUG assignments
    pattern = re.compile(
        r'^(\s*(?:LOCAL_|BUILDER_)?[A-Z_]*DEBUG\s*=\s*)(True|False)(.*)$', 
        re.MULTILINE
    )
    
    py_files = []
    for root, dirs, files in os.walk(project_root):
        # Respect project boundaries and ignore hidden/temporary directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and 
                  d not in ['venv', 'node_modules', '__pycache__', 'oaDataLogs']]
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
            def _debug_mode_wrapper(match):
                nonlocal replacements_made
                current_value = match.group(2)
                # Only replace if the state is different to avoid disk churn
                if current_value != target_state_str:
                    replacements_made += 1
                    return f"{match.group(1)}{target_state_str}{match.group(3)}"
                return match.group(0)

            new_content = pattern.sub(_debug_mode_wrapper, content)
            
            if replacements_made > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                files_modified += 1
                flags_changed += replacements_made
        except Exception as e:
            logger.error(f"⚠️ [CONFIG] Failed to process {file_path.name}: {e}")

    if files_modified > 0:
        logger.success(f"🚀 [DEPLOY] {action} complete. "
                       f"Changed {flags_changed} flags across {files_modified} files.")
        return True
    
    logger.info(f"🛌 [SLEEPING] No state change needed. "
                f"All flags already {target_state_str.upper()}.")
    return False

def force_debug_on(project_root, console_print_func=None):
    """Forces all recognized debug flags to True."""
    return _set_debug_state(project_root, True, console_print_func)

def force_debug_off(project_root, console_print_func=None):
    """Forces all recognized debug flags to False."""
    return _set_debug_state(project_root, False, console_print_func)

def toggle_debug_flags(project_root, console_print_func=None):
    """
    Toggles all debug flags based on the state of the first flag encountered.

    This implements a 'Flip-Flop' logic: if the first file scanned has 
    debug enabled, the entire project is set to disabled, and vice-versa.
    """
    pattern = re.compile(r'^\s*(?:LOCAL_|BUILDER_)?[A-Z_]*DEBUG\s*=\s*(True|False)', 
                        re.MULTILINE)
    
    current_state_found = None
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if not d.startswith('.') and 
                  d not in ['venv', 'node_modules', '__pycache__']]
        for file in files:
            if file.endswith('.py'):
                try:
                    with open(Path(root) / file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    match = pattern.search(content)
                    if match:
                        current_state_found = (match.group(1) == "True")
                        break
                except Exception:
                    continue
        if current_state_found is not None:
            break

    if current_state_found is None:
        return force_debug_on(project_root, console_print_func)
    
    return _set_debug_state(project_root, not current_state_found, console_print_func)

if __name__ == "__main__":
    # Resolve the project root relative to this utility's location
    project_root_path = Path(__file__).resolve().parents[2]
    toggle_debug_flags(project_root_path)
oot_path)
ect_root_path = Path(__file__).resolve().parents[2]
    toggle_debug_flags(project_root_path)
oot_path)
ct_root_path)
= Path(__file__).resolve().parents[2]
    toggle_debug_flags(project_root_path)
