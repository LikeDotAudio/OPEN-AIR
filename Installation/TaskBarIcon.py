# Installation/TaskBarIcon.py
#
# Configures and installs the OPEN-AIR desktop entry and GNOME favorites icon.
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
# Version 20260314.002000.REV01

"""
Primary Purpose:
Provides automated installation of the OPEN-AIR application icon into the Linux
desktop environment. It handles the deployment of the .desktop entry and
attempts to pin the application to the GNOME Shell favorites bar.

Hard Constraints:
- Platform Dependency: Specifically targeted at Linux distributions using GNOME
  Shell (utilizes 'gsettings').
- Privileges: Requires write access to the user's local applications directory
  (~/.local/share/applications).
- System State: Assumes the existence of 'OPEN-AIR.desktop' in the same folder.
"""

import os
import shutil
import subprocess
import sys
import ast

# --- Standard Debug Logging Setup ---
# LOCAL_DEBUG: Toggles verbose logging for icon installation diagnostics.
LOCAL_DEBUG = True
from loguru import logger

def install_icon():
    """
    Deploys the application's desktop entry and updates GNOME favorites.

    Lead with action: Orchestrates the copying of the .desktop file to the
    appropriate user directory and invokes GNOME configuration tools to update
    the taskbar.

    Inputs:
        None.

    Outputs:
        None. Success is indicated via log entries; failures result in early
        return with error logs.

    Side Effects:
        - Creates the '~/.local/share/applications' directory if missing.
        - Writes a file to the filesystem.
        - Modifies GNOME Shell global preferences via 'gsettings'.
    
    Thread Safety:
        Not thread-safe. Intended to be run as a standalone installation script.
    """
    # Define local pathing relative to the script's execution context.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    source_desktop_file = os.path.join(current_dir, 'OPEN-AIR.desktop')
    
    # Standard location for per-user desktop entries on Linux.
    user_applications_dir = os.path.expanduser('~/.local/share/applications')
    dest_desktop_file = os.path.join(user_applications_dir, 'OPEN-AIR.desktop')
    
    # 1. Install .desktop file
    if not os.path.exists(user_applications_dir):
        try:
            # Ensure the directory tree exists before attempting file copy.
            os.makedirs(user_applications_dir)
        except OSError as e:
            # Gravity of Errors: Non-gated failure reporting for system I/O.
            logger.error(f"🖥️🖱️🎨 [DESKTOP] ERROR: Failed to create "
                         f"applications dir: {e}")
            return

    if not os.path.exists(source_desktop_file):
        logger.error(f"🖥️🖱️🎨 [DESKTOP] ERROR: Source file not found: "
                     f"{source_desktop_file}")
        return
        
    if LOCAL_DEBUG:
        logger.debug(f"🖥️🖱️🎨 [DESKTOP] Installing {source_desktop_file} "
                     f"to {dest_desktop_file}...")
    try:
        shutil.copy(source_desktop_file, dest_desktop_file)
        # Ensure the file is executable so the desktop environment can launch it.
        os.chmod(dest_desktop_file, 0o755)
        if LOCAL_DEBUG:
            logger.success("✅✅✅ [SUCCESS] Desktop file installed.")
    except Exception as e:
        logger.error(f"🖥️🖱️🎨 [DESKTOP] ERROR: File install failed: {e}")
        return

    # 2. Add to Taskbar (GNOME Favorites)
    # This section specifically targets GNOME Shell's 'favorite-apps' schema.
    try:
        # Check if gsettings is available to avoid shell errors.
        if shutil.which('gsettings') is None:
            if LOCAL_DEBUG:
                logger.warning("🖥️🖱️🎨 [DESKTOP] 'gsettings' not found. "
                               "Skipping taskbar pin.")
            return

        # Retrieve the current list of pinned applications.
        result = subprocess.run(
            ['gsettings', 'get', 'org.gnome.shell', 'favorite-apps'],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            logger.error("🖥️🖱️🎨 [DESKTOP] ERROR: Could not retrieve GNOME "
                         "favorites.")
            return

        current_favorites_str = result.stdout.strip()
        
        # Parse the gsettings string representation (which looks like a list).
        if not current_favorites_str or current_favorites_str == "@as []":
            current_favorites = []
        else:
            try:
                # Use literal_eval for safe parsing of the list-like string.
                current_favorites = ast.literal_eval(current_favorites_str)
            except (ValueError, SyntaxError):
                logger.error(f"🖥️🖱️🎨 [DESKTOP] ERROR: Failed to parse "
                             f"favorites: {current_favorites_str}")
                return

        desktop_filename = 'OPEN-AIR.desktop'
        
        if desktop_filename in current_favorites:
            if LOCAL_DEBUG:
                logger.info("🖥️🖱️🎨 [DESKTOP] Application already in "
                            "favorites.")
        else:
            if LOCAL_DEBUG:
                logger.debug("🖥️🖱️🎨 [DESKTOP] Adding to GNOME favorites...")
            current_favorites.append(desktop_filename)
            # Re-serialize the list back to the format gsettings expects.
            new_favorites_str = str(current_favorites)
            
            subprocess.run(
                ['gsettings', 'set', 'org.gnome.shell', 'favorite-apps', 
                 new_favorites_str],
                check=True
            )
            if LOCAL_DEBUG:
                logger.success("✅✅✅ [SUCCESS] Added to GNOME taskbar.")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"🖥️🖱️🎨 [DESKTOP] ERROR: gsettings failure: {e}")
    except Exception as e:
        logger.exception("🖥️🖱️🎨 [DESKTOP] CRITICAL: Unexpected error during "
                         "taskbar pinning.")

if __name__ == "__main__":
    install_icon()
