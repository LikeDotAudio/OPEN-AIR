#!/usr/bin/env python3
# workers/logger/set_debug_state.py
#
# Standardized Debug State Toggler for OPEN-AIR (Python Version).
# Scans for variables ending in _DEBUG and flips or sets their boolean state.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your
# specific application can be negotiated. There is no charge to use, modify,
# or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260314.013500.REV01

"""
Primary Purpose:
Provides a cross-platform utility to bulk-modify debugging flags across the
entire OPEN-AIR Python codebase. This script is designed to be called by 
CI/CD pipelines or developer convenience commands (like 'UpdateDebug') to 
toggle diagnostic verbosity.

Hard Constraints:
- Permissions: Requires write access to target files in the directory tree.
- Regex: Only matches flags at the start of a line to avoid false positives 
  within strings or nested logic.
- Encoding: Assumes UTF-8 encoded source files.
"""

import os
import sys
import re
import argparse

def log(msg, color="\033[0m"):
    """
    Outputs a formatted message to the terminal with ANSI color support.

    Inputs:
        msg (str): The text message to display.
        color (str): The ANSI escape sequence for the desired color. 
            Defaults to RESET (\033[0m).

    Outputs:
        None. Displays text via sys.stdout.
    """
    # Simple colored print for terminal diagnostics.
    print(f"{color}{msg}\033[0m")

def update_debug_flags(target_dir, set_to=None):
    """
    Recursively updates debug flag assignments in Python source files.

    Lead with action: Walk the directory tree, parse each .py file for
    flag patterns, and apply boolean state transitions.

    Inputs:
        target_dir (str): Absolute path to the directory to be scanned.
        set_to (str, optional): Explicit state to force ('True' or 'False').
            If NULL, the script toggles the existing state of each flag.

    Outputs:
        None.
    
    Side Effects:
        - Performs recursive filesystem traversal.
        - Modifies file contents in-place.
        - Generates log output to the terminal.
    """
    log(f"💓🫀🔄 [WATCHDOG] Scanning for _DEBUG heartbeat flags in "
        f"{target_dir}...", "\033[36m")
    
    # Standard Pattern: LOCAL_DEBUG or uppercase variable names suffixed with _DEBUG.
    # Anchored to line starts to minimize collateral damage.
    pattern = re.compile(r'^(LOCAL_DEBUG|[A-Z0-9_]+_DEBUG)\s*=\s*(True|False)', re.MULTILINE)
    
    update_count = 0
    file_count = 0

    for root, dirs, files in os.walk(target_dir):
        # Prune hidden directories like .git to optimize scan time.
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if file.endswith(".py"):
                file_count += 1
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception as e:
                    log(f"⚠️ Error reading {file}: {e}", "\033[31m")
                    continue
                
                new_content = content
                matches = list(pattern.finditer(content))
                
                if not matches:
                    continue
                    
                file_updated = False
                for match in matches:
                    var_name = match.group(1)
                    current_val = match.group(2)
                    
                    if set_to is not None:
                        new_val = set_to
                    else:
                        # Toggle logic: Flip the current boolean literal.
                        new_val = "False" if current_val == "True" else "True"
                    
                    # redudancy check prevents unnecessary disk writes.
                    if current_val != new_val:
                        # Replace only the exact matched sequence.
                        new_line = f"{var_name} = {new_val}"
                        new_content = new_content.replace(match.group(0), new_line)
                        
                        log(f"⚡ Flip: {file} -> {var_name} set to {new_val}", 
                            "\033[33m")
                        file_updated = True
                        update_count += 1
                
                if file_updated:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)

    log(f"✅🆗✅ [SUCCESS] Global state transition complete. Updated "
        f"{update_count} flags in {file_count} files.", "\033[32m")

if __name__ == "__main__":
    # Standard CLI interface for standalone execution.
    parser = argparse.ArgumentParser(
        description="Toggle or set _DEBUG flags in Python files."
    )
    parser.add_argument("--state", choices=["True", "False"], 
                        help="Force state to True or False")
    parser.add_argument("--dir", default=".", 
                        help="Target directory (defaults to current)")
    
    args = parser.parse_args()
    
    # Ensure we are working with absolute paths for clarity in logs.
    target_abs_path = os.path.abspath(args.dir)
    
    update_debug_flags(target_abs_path, args.state)
