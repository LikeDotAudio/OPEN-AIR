import inspect
import os
import sys

# --- Path Injection ---
# We must calculate the project root and add it to sys.path to ensure that
# this script can be executed directly while still finding project modules.
current_dir = os.path.dirname(os.path.abspath(__file__))
# Assumes Core/ is inside oaInstallation/, and oaInstallation/ is at the root.
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from oaLogging.Methods.matrix_gate import matrix_log

# Core/TaskBarIcon.py
# Author: Anthony Peter Kuzub
# Version: 20260314.002000.REV01
#
# Description: Configures and installs the OPEN-AIR desktop entry and GNOME favorites icon.

"""
Primary Purpose:
Provides automated installation of the OPEN-AIR application icon into the Linux
desktop environment.
"""

import ast
import shutil
import subprocess

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False
from loguru import logger

# --- Constants ---
VERSION = "20260314.002000.REV01"
DESKTOP_FILENAME = 'OPEN-AIR.desktop'

def install_icon():
    """
    Deploys the application's desktop entry and updates GNOME favorites.
    """
    # Define local pathing relative to the script's execution context.
    # The .desktop file is stored in the module's Assets directory.
    core_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.abspath(os.path.join(core_dir, "..", "Assets"))
    source_desktop_file = os.path.join(assets_dir, DESKTOP_FILENAME)

    # Standard location for per-user desktop entries on Linux.
    user_applications_dir = os.path.expanduser('~/.local/share/applications')
    dest_desktop_file = os.path.join(user_applications_dir, DESKTOP_FILENAME)

    # 1. Install .desktop file
    if not os.path.exists(user_applications_dir):
        try:
            # Ensure the directory tree exists before attempting file copy.
            os.makedirs(user_applications_dir)
        except OSError as os_error:
            # Gravity of Errors: Non-gated failure reporting for system I/O.
            logger.error(f"🖥️🖱️🎨 [DESKTOP] ERROR: Failed to create "
                         f"applications dir: {os_error}")
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
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "✅✅✅ [SUCCESS] Desktop file installed.", "SUCCESS")
    except Exception as install_error:
        logger.error(f"🖥️🖱️🎨 [DESKTOP] ERROR: File install failed: {install_error}")
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

        if DESKTOP_FILENAME in current_favorites:
            if LOCAL_DEBUG:
                logger.info("🖥️🖱️🎨 [DESKTOP] Application already in "
                            "favorites.")
        else:
            if LOCAL_DEBUG:
                matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🖥️🖱️🎨 [DESKTOP] Adding to GNOME favorites...", "DEBUG")
            current_favorites.append(DESKTOP_FILENAME)
            # Re-serialize the list back to the format gsettings expects.
            new_favorites_str = str(current_favorites)

            subprocess.run(
                ['gsettings', 'set', 'org.gnome.shell', 'favorite-apps',
                 new_favorites_str],
                check=True
            )
            if LOCAL_DEBUG:
                matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "✅✅✅ [SUCCESS] Added to GNOME taskbar.", "SUCCESS")

    except subprocess.CalledProcessError as process_error:
        logger.error(f"🖥️🖱️🎨 [DESKTOP] ERROR: gsettings failure: {process_error}")
    except Exception:
        logger.exception("🖥️🖱️🎨 [DESKTOP] CRITICAL: Unexpected error during "
                         "taskbar pinning.")

if __name__ == "__main__":
    install_icon()
